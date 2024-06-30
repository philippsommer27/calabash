import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def power_plot(dfs, output_path, show=False, title='Power consumption over time'):
    sns.set_theme()
    line_styles = ['-', '--', '-.', ':']
    
    # Create a plot
    plt.figure(figsize=(12, 8))
    
    # Loop through each data frame and plot
    for i, df in enumerate(dfs):
        line_style = line_styles[i % len(line_styles)]  # Cycle through line styles
        sns.lineplot(x='timestamp', y='consumption', data=df, linestyle=line_style, label=f'DF{i+1}')
    
    # Customize the plot
    plt.xlabel('Time (s)')
    plt.ylabel('Power (W)')
    plt.title(title)
    plt.legend(title='DataFrame')
    
    # Save or show the plot
    if show:
        plt.show()
    plt.savefig(output_path)

def boxplot(dfs, column_name, output_path):
    combined_df = pd.DataFrame()

    for i, df in enumerate(dfs):
        df_temp = df[[column_name]].copy()
        df_temp['Variation'] = f'Var{i+1}'
        combined_df = pd.concat([combined_df, df_temp], axis=0)

    plt.figure(figsize=(10, 6))
    sns.boxplot(x='Variation', y=column_name, data=combined_df)
    plt.savefig(output_path)

