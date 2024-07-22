import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

def set_plot_theme():
    sns.set_theme()
    plt.rcParams['font.family'] = 'FreeSerif'
    plt.rcParams['font.size'] = 14

def concatenate_dataframes(dfs):
    for df in dfs:
        df.reset_index(inplace=True)
    return pd.concat(dfs, ignore_index=True)

def save_plot(output_path, formats=('png', 'pdf')):
    for fmt in formats:
        plt.savefig(f"{output_path}.{fmt}", format=fmt, bbox_inches='tight')

def power_plot(dfs, output_path, show=False, title='Heatmap of power consumption over time'):
    set_plot_theme()
    
    combined_df = concatenate_dataframes(dfs)
    
    plt.figure(figsize=(10, 6))
    ax = sns.kdeplot(data=combined_df, x='timestamp', y='consumption', cmap="rocket_r", fill=True, bw_adjust=.5, levels=50)
    
    plt.xlabel('Time (s)')
    plt.ylabel('Power (W)')
    plt.title(title)

    rocket_cmap = sns.color_palette("rocket_r", as_cmap=True)
    ax.set_facecolor(rocket_cmap(0))
    ax.grid(False)
    
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    if show:
        plt.show()
    save_plot(output_path)
    
def distribution_plot(dfs, column_name, output_path, column_nice_name):
    set_plot_theme()
    
    combined_df = pd.DataFrame()
    for i, df in enumerate(dfs):
        df_temp = df[[column_name]].copy()
        df_temp['Variation'] = f'V{i+1}'
        combined_df = pd.concat([combined_df, df_temp], axis=0)
    
    n_colors = len(dfs)
    color_palette = sns.color_palette("deep", n_colors=n_colors)
    
    def set_y_limits(ax, bottom=0, top_factor=1.1):
        y_min, y_max = ax.get_ylim()
        ax.set_ylim(bottom=bottom, top=y_max * top_factor)
    
    def get_figure_width(n_variations, min_width=6, max_width=12, width_per_variation=1.5):
        return min(max(n_variations * width_per_variation, min_width), max_width)
    
    figure_width = get_figure_width(n_colors)
    
    plt.figure(figsize=(figure_width, 6))
    ax = sns.violinplot(data=combined_df, x='Variation', hue='Variation', y=column_name, palette=color_palette, legend=False)
    set_y_limits(ax)
    ax.set_ylabel(column_nice_name)
    save_plot(output_path + '_violin')
    
    plt.figure(figsize=(10, 6))
    ax = sns.kdeplot(data=combined_df, x=column_name, hue='Variation', fill=True, 
                     common_norm=True, palette=color_palette, legend=False)
    set_y_limits(ax)
    ax.set_xlabel(column_nice_name)
    save_plot(output_path + '_kde')
    
    plt.figure(figsize=(figure_width, 6))
    ax = sns.boxplot(data=combined_df, x='Variation', y=column_name, hue='Variation', palette=color_palette, legend=False)
    set_y_limits(ax)
    ax.set_ylabel(column_nice_name)
    save_plot(output_path + '_box')