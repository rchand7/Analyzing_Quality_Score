import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Function to calculate quality score in percentage
def calculate_quality_score_percentage(critical_errors, non_critical_errors, sample):
    quality_score = 1 - ((non_critical_errors / 4 + critical_errors) / sample)
    return round(quality_score * 100, 2)

# Streamlit app
def main():
    st.title("AR Audit Report Summary")

    # Upload file
    uploaded_file = st.file_uploader("Upload Excel file", type=['xlsx', 'xls'])

    if uploaded_file is not None:
        # Read the Excel file
        ar_df = pd.read_excel(uploaded_file)

        # Convert 'EmpID' column to strings
        ar_df['EmpID'] = ar_df['EmpID'].astype(str)

        # Remove commas from 'EmpID'
        ar_df['EmpID'] = ar_df['EmpID'].str.replace(',', '')

        # Convert 'EmpID' strings to float to handle NaN values
        ar_df['EmpID'] = ar_df['EmpID'].astype(float)

        # Fill NaN values with a placeholder (-1)
        ar_df['EmpID'] = ar_df['EmpID'].fillna(-1)

        try:
            # Convert 'EmpID' floats to integers
            ar_df['EmpID'] = ar_df['EmpID'].astype(int)
        except pd.errors.IntCastingNaNError:
            st.error("Error: Cannot convert non-finite values (NA or inf) to integer in 'EmpID' column.")
            return

        # Filter out rows with blank 'AnalystName'
        ar_df = ar_df[ar_df['AnalystName'].notna()]

        # Create a list to hold summary data
        summary_data = []

        # Group by EmpID
        grouped_df = ar_df.groupby('EmpID')

        # Iterate over groups
        for emp_id, group in grouped_df:
            analyst_name = group['AnalystName'].iloc[0]
            sample = len(group)
            critical_errors = sum(group['UE Score'] == 0)
            non_critical_errors = sum(group['UE Score'] == 75)
            quality_score = calculate_quality_score_percentage(critical_errors, non_critical_errors, sample)

            # Append data to summary list
            summary_data.append({
                "EmpID": emp_id,
                "AnalystName": analyst_name,
                "Sample": sample,
                "Critical Error": critical_errors,
                "Non-Critical Error": non_critical_errors,
                "Quality Score": quality_score
            })

        # Create DataFrame from summary data
        summary_df = pd.DataFrame(summary_data)

        # Sort DataFrame by 'Quality Score' in descending order
        summary_df = summary_df.sort_values(by='Quality Score', ascending=False)

        # Calculate totals
        total_sample = summary_df['Sample'].sum()
        total_critical_errors = summary_df['Critical Error'].sum()
        total_non_critical_errors = summary_df['Non-Critical Error'].sum()
        avg_quality_score = summary_df['Quality Score'].mean()

        # Create DataFrame for total row
        total_row = pd.DataFrame({
            "EmpID": ["Total"],
            "Sample": [total_sample],
            "Critical Error": [total_critical_errors],
            "Non-Critical Error": [total_non_critical_errors],
            "Quality Score": [round(avg_quality_score, 2)]
        })

        # Concatenate total row with summary DataFrame
        summary_df = pd.concat([summary_df, total_row], ignore_index=True)

        # Display the summary table
        st.write("Summary Table:")
        st.write(summary_df)

        if 'AnalystName' in summary_df.columns:  
            analyst_name_list = summary_df['AnalystName'].unique().tolist()
            if 'group_notification' in analyst_name_list:
                analyst_name_list.remove('group_notification')
            analyst_name_list = [str(analyst_name) for analyst_name in analyst_name_list]
            analyst_name_list.sort()
            analyst_name_list.insert(0, "Overall")  

            selected_analyst_name = st.sidebar.selectbox("Show analysis wrt", analyst_name_list)

            if st.sidebar.button("Show Analysis"):
                if selected_analyst_name == "Overall":
                    st.write("Analyzing Overall Statistics")
                    mean_sample = summary_df['Sample'].mean()
                    median_sample = summary_df['Sample'].median()
                    mode_sample = summary_df['Sample'].mode().iloc[0]
                    std_sample = summary_df['Sample'].std()
                    
                    st.write(f"Mean of Sum of Sample: {mean_sample}")
                    st.write(f"Median of Sum of Sample: {median_sample}")
                    st.write(f"Mode of Sum of Sample: {mode_sample}")
                    st.write(f"Standard Deviation of Sum of Sample: {std_sample}")

                    # Visualize the data
                    st.subheader("Histogram of Sum of Sample")
                    fig, ax = plt.subplots()
                    ax.hist(summary_df['Sample'], bins=10, color='skyblue', edgecolor='black')
                    st.pyplot(fig)

                    # Add more visualizations and statistical analysis as needed
                else:
                    st.write(f"Analyzing {selected_analyst_name}'s Statistics")
                    selected_analyst_df = ar_df[ar_df['AnalystName'] == selected_analyst_name]

                    # Filter comments based on UE Score
                    non_critical_comments = selected_analyst_df[selected_analyst_df['UE Score'] == 75][['BSO QA Detailed Comments']]
                    critical_comments = selected_analyst_df[selected_analyst_df['UE Score'] == 0][['BSO QA Detailed Comments']]

                    # Display comments and error counts in a table format
                    st.subheader("Non-Critical Error Comments:")
                    st.table(non_critical_comments)
                    st.write(f"Error Count: {len(non_critical_comments)}")

                    st.subheader("Critical Error Comments:")
                    st.table(critical_comments)
                    st.write(f"Error Count: {len(critical_comments)}")

    else:
        st.error("The uploaded file does not contain an 'Emp Name' column.")

# Run the app
if __name__ == "__main__":
    main()
