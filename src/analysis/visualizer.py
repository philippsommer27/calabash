import matplotlib.pyplot as plt
import seaborn as sns

def power_plot(df, output_path, show=False, title='Power consumption over time'):
    sns.set_theme()

    sns.plot(df['timestamp'], df['consumption'])
    sns.xlabel('Time (s)')
    sns.ylabel('Power (W)')
    sns.title(title)
    if show:    
        sns.show()
    sns.savefig(output_path)