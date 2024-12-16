import streamlit as st

pg = st.navigation(
    {
        "BACKTESTING": [
            st.Page("2_experiments.py", title="Simulation Experiments", icon="🧪"),
            st.Page("3_optimization.py", title="Strategy Optimization", icon="🧬"),
        ],
        "REAL-TIME": [
            st.Page("4_deployment.py", title="Deployment", icon="🚀"),
        ],
    },
)
pg.run()
