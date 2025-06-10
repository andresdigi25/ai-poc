import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from app.core.config import settings
from app.models.document import Document
import plotly.express as px
from datetime import datetime, timedelta

# Database connection
engine = create_engine(settings.DATABASE_URL)

def load_documents():
    """Load documents from the database."""
    query = "SELECT * FROM documents"
    return pd.read_sql(query, engine)

def main():
    st.title("Talk to Docs Dashboard")
    
    # Load data
    documents = load_documents()
    
    # Overview metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Documents", len(documents))
    with col2:
        completed = len(documents[documents['status'] == 'completed'])
        st.metric("Completed", completed)
    with col3:
        success_rate = (completed / len(documents) * 100) if len(documents) > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    # Status distribution
    st.subheader("Document Processing Status")
    status_counts = documents['status'].value_counts()
    fig = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title="Document Processing Status Distribution"
    )
    st.plotly_chart(fig)
    
    # Processing timeline
    st.subheader("Processing Timeline")
    documents['created_at'] = pd.to_datetime(documents['created_at'])
    timeline = documents.groupby(documents['created_at'].dt.date).size().reset_index()
    timeline.columns = ['date', 'count']
    fig = px.line(
        timeline,
        x='date',
        y='count',
        title="Documents Processed Over Time"
    )
    st.plotly_chart(fig)
    
    # Document list
    st.subheader("Recent Documents")
    recent_docs = documents.sort_values('created_at', ascending=False).head(10)
    for _, doc in recent_docs.iterrows():
        with st.expander(f"{doc['filename']} ({doc['status']})"):
            st.write(f"Created: {doc['created_at']}")
            if doc['summary']:
                st.write("Summary:")
                st.write(doc['summary'])
            if doc['metadata']:
                st.write("Metadata:")
                st.json(doc['metadata'])

if __name__ == "__main__":
    main() 