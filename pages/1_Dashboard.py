# ---------------- CHARTS ----------------
col5, col6 = st.columns(2)

# --- Chart 1: Tonality Distribution ---
with col5:
    st.markdown("<div class='chart-tile'>", unsafe_allow_html=True)
    st.subheader("Tonality Distribution")
    tonality_counts = filtered["tonality"].value_counts().reset_index()
    tonality_counts.columns = ["Tonality", "Count"]
    if not tonality_counts.empty:
        fig_donut = px.pie(
            tonality_counts,
            names="Tonality",
            values="Count",
            hole=0.5,  # doughnut style
            color="Tonality",
            color_discrete_map={
                "Positive": HELB_GREEN,
                "Negative": HELB_RED,
                "Neutral": HELB_GREY,
            },
        )
        fig_donut.update_traces(
            textposition="inside",
            textinfo="percent+label",
            insidetextfont=dict(color="white"),
        )
        st.plotly_chart(fig_donut, use_container_width=True)
    else:
        st.info("No data for selected filters.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- Chart 2: Mentions Over Time ---
with col6:
    st.markdown("<div class='chart-tile'>", unsafe_allow_html=True)
    st.subheader("Mentions Over Time")
    timeline = filtered.groupby(filtered["published_parsed"].dt.date).size().reset_index(name="Count")
    if not timeline.empty:
        fig_line = px.line(timeline, x="published_parsed", y="Count", markers=True)
        fig_line.update_traces(line_color=HELB_BLUE)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No data for selected filters.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- Chart 3: Top Sources ---
col7, col8 = st.columns(2)
with col7:
    st.markdown("<div class='chart-tile'>", unsafe_allow_html=True)
    st.subheader("Top News Sources")
    top_sources = filtered["source"].value_counts().head(7).reset_index()
    top_sources.columns = ["Source", "Count"]
    if not top_sources.empty:
        fig_bar = px.bar(
            top_sources,
            x="Count",
            y="Source",
            orientation="h",
            title="",
            color="Count",
            color_continuous_scale=[HELB_GREEN, HELB_BLUE],
        )
        fig_bar.update_layout(yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No data for selected filters.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- Chart 4: Tonality Trend Over Time ---
with col8:
    st.markdown("<div class='chart-tile'>", unsafe_allow_html=True)
    st.subheader("Tonality Trend Over Time")
    if not filtered.empty:
        trend = (
            filtered.groupby([filtered["published_parsed"].dt.to_period("M"), "tonality"])
            .size()
            .reset_index(name="Count")
        )
        trend["published_parsed"] = trend["published_parsed"].astype(str)
        fig_area = px.area(
            trend,
            x="published_parsed",
            y="Count",
            color="tonality",
            color_discrete_map={
                "Positive": HELB_GREEN,
                "Negative": HELB_RED,
                "Neutral": HELB_GREY,
            },
        )
        st.plotly_chart(fig_area, use_container_width=True)
    else:
        st.info("No data for selected filters.")
    st.markdown("</div>", unsafe_allow_html=True)
