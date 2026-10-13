import requests
import streamlit as st

st.set_page_config(
    page_title="Review Analyzer",
    page_icon="💬",
    layout="centered",
)

st.markdown(
    """
    <style>
      .block-container {max-width: 760px; padding-top: 3rem;}
      .hero {padding: 1.5rem 0 1rem;}
      .hero h1 {margin-bottom: .35rem;}
      .hero p {color: #64748b; font-size: 1.05rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("Connection")
    api_url = st.text_input(
        "FastAPI address",
        value="http://127.0.0.1:8000",
        help="Start the FastAPI server before analyzing reviews.",
    ).strip().rstrip("/")
    st.caption("Reviews and their analyses are saved in feedback.db.")

st.markdown(
    """
    <div class="hero">
      <h1>Review Analyzer</h1>
      <p>Analyze customer reviews and keep a searchable record of the results.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("review_form"):
    review_text = st.text_area(
        "Customer reviews",
        placeholder=(
            "The food was delicious, but delivery was very slow.\n"
            "Amazing taste and the order arrived hot.\n"
            "Prices are too high for the small portion."
        ),
        help="Enter one review per line. Blank lines are ignored.",
        height=180,
        max_chars=5000,
    )
    submitted = st.form_submit_button(
        "Analyze and save",
        type="primary",
        use_container_width=True,
    )

if submitted:
    reviews = [line.strip() for line in review_text.splitlines() if line.strip()]

    if not reviews:
        st.warning("Enter at least one review, with one review per line.")
    elif not api_url:
        st.warning("Enter the address of your FastAPI server in the sidebar.")
    else:
        results = []
        failures = []
        connection_failed = False

        with st.spinner(f"Analyzing and saving {len(reviews)} review(s)…"):
            for index, review in enumerate(reviews, start=1):
                try:
                    response = requests.post(
                        f"{api_url}/analyze",
                        json={"text": review},
                        timeout=45,
                    )
                    if not response.ok:
                        try:
                            detail = response.json().get("detail", response.text)
                        except ValueError:
                            detail = response.text
                        failures.append(f"Review {index}: HTTP {response.status_code}: {detail}")
                        continue

                    result = response.json()
                    results.append(
                        {
                            "Review": review,
                            "Sentiment": str(result["label"]).strip().capitalize(),
                            "Score": f"{int(result['score'])} / 5",
                            "Main topic": str(result["theme"]).strip().capitalize(),
                        }
                    )
                except requests.exceptions.ConnectionError:
                    failures.append(
                        f"Could not reach the API while processing review {index}. "
                        "Start it with `uv run fastapi dev api.py`."
                    )
                    connection_failed = True
                    break
                except requests.exceptions.Timeout:
                    failures.append(f"Review {index}: the request timed out.")
                except (ValueError, KeyError, TypeError):
                    failures.append(f"Review {index}: the API returned an unexpected response.")
                except requests.exceptions.RequestException as exc:
                    failures.append(f"Review {index}: {exc}")

        if results:
            st.success(f"Analyzed and saved {len(results)} of {len(reviews)} review(s).")
            st.dataframe(results, hide_index=True, use_container_width=True)
        if failures:
            st.warning(f"{len(failures)} review(s) could not be processed.")
            for message in failures:
                st.error(message)

with st.expander("View saved feedback"):
    if st.button("Load saved feedback", key="load_feedback"):
        if not api_url:
            st.warning("Enter the address of your FastAPI server in the sidebar.")
        else:
            try:
                response = requests.get(f"{api_url}/feedback", timeout=15)
                if not response.ok:
                    st.error(f"Could not load feedback (HTTP {response.status_code}).")
                else:
                    records = response.json()
                    if records:
                        st.dataframe(
                            [
                                {
                                    "Date (UTC)": item["created_at"],
                                    "Feedback": item["text"],
                                    "Sentiment": item["label"].capitalize(),
                                    "Score": f"{item['score']} / 5",
                                    "Theme": item["theme"].capitalize(),
                                }
                                for item in records
                            ],
                            hide_index=True,
                            use_container_width=True,
                        )
                    else:
                        st.info("No feedback has been saved yet.")
            except requests.exceptions.RequestException:
                st.error("Could not reach the FastAPI server to load saved feedback.")
            except (ValueError, KeyError, TypeError):
                st.error("The API returned an unexpected feedback response.")

st.caption("Sentiment labels: positive, neutral, or negative · Score: 1 to 5")
