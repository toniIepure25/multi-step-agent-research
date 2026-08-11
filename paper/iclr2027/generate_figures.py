"""Generate publication-quality figures for the ICLR 2027 submission.

Requires: matplotlib, numpy
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

FIGDIR = os.path.join(os.path.dirname(__file__), 'figures')
os.makedirs(FIGDIR, exist_ok=True)

CB_BLUE = '#0072B2'
CB_ORANGE = '#E69F00'
CB_GREEN = '#009E73'
CB_RED = '#D55E00'
CB_PURPLE = '#CC79A7'
CB_GRAY = '#999999'


def fig2_complementarity_matrix():
    """Pairwise complementarity heatmap from V4 data."""
    ops = ['Retrieve', 'Hypothesize', 'Attack', 'Reason']
    matrix = np.array([
        [-0.002, +0.078, +0.025, +0.025],
        [+0.162, -0.050, +0.137, +0.137],
        [+0.025, +0.137, +0.000, +0.000],
        [+0.025, +0.137, +0.000, +0.000],
    ])

    fig, ax = plt.subplots(figsize=(4.5, 3.5))
    cmap = plt.cm.RdBu_r
    im = ax.imshow(matrix, cmap=cmap, vmin=-0.15, vmax=0.20, aspect='equal')

    ax.set_xticks(range(4))
    ax.set_yticks(range(4))
    ax.set_xticklabels(ops, fontsize=9)
    ax.set_yticklabels(ops, fontsize=9)
    ax.set_xlabel('Second operation', fontsize=10)
    ax.set_ylabel('First operation', fontsize=10)

    for i in range(4):
        for j in range(4):
            val = matrix[i, j]
            color = 'white' if abs(val) > 0.10 else 'black'
            ax.text(j, i, f'{val:+.3f}', ha='center', va='center',
                    fontsize=8, color=color, fontweight='bold' if abs(val) > 0.10 else 'normal')

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Complementarity', fontsize=9)
    ax.set_title('Pairwise Temporal Complementarity (N=56)', fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'fig2_complementarity.pdf'), dpi=300, bbox_inches='tight')
    fig.savefig(os.path.join(FIGDIR, 'fig2_complementarity.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print('  fig2_complementarity: saved')


def fig3_attack_timing():
    """Attack value vs epistemic stage."""
    stages = ['Standalone\n(no context)', 'After\nRetrieve', 'After\nHyp+Ret', 'After\nHyp+Ret+Rsn']
    sim_values = [0.000, 0.025, 0.137, 0.137]
    llm_values = [0.000, None, 0.276, None]

    fig, ax = plt.subplots(figsize=(5, 3.2))
    x = np.arange(len(stages))
    width = 0.35

    bars_sim = ax.bar(x - width/2, sim_values, width, label='Simulator (N=56)',
                       color=CB_BLUE, edgecolor='white', linewidth=0.5)

    llm_plot = [v if v is not None else 0 for v in llm_values]
    llm_colors = [CB_ORANGE if v is not None else 'none' for v in llm_values]
    bars_llm = ax.bar(x + width/2, llm_plot, width, label='LLM (N=16)',
                       color=llm_colors, edgecolor=['white' if v is not None else 'none' for v in llm_values],
                       linewidth=0.5)

    ax.set_ylabel('Quality contribution', fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels(stages, fontsize=8)
    ax.legend(fontsize=8, loc='upper left')
    ax.set_ylim(-0.02, 0.35)
    ax.axhline(y=0, color='gray', linewidth=0.5, linestyle='-')
    ax.set_title('Attack/Falsification Value by Epistemic Stage', fontsize=10)
    ax.annotate('Zero standalone\nvalue', xy=(0, 0.005), fontsize=7, color=CB_RED, ha='center')
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'fig3_attack_timing.pdf'), dpi=300, bbox_inches='tight')
    fig.savefig(os.path.join(FIGDIR, 'fig3_attack_timing.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print('  fig3_attack_timing: saved')


def fig4_adaptive_control():
    """Oracle vs fixed vs learned adaptive control."""
    categories = ['Oracle\n(per-world best)', 'Best fixed\n(B1_extended)', 'Learned\nadaptive']
    values = [0.588, 0.518, 0.323]
    colors = [CB_GREEN, CB_BLUE, CB_RED]
    errors = [0.04, 0.05, 0.06]

    fig, ax = plt.subplots(figsize=(4.5, 3.2))
    bars = ax.bar(categories, values, color=colors, edgecolor='white', linewidth=0.5,
                   yerr=errors, capsize=4, error_kw={'linewidth': 1.0})

    ax.set_ylabel('Mean epistemic quality', fontsize=10)
    ax.set_ylim(0, 0.75)
    ax.set_title('Adaptive Control Failure (N=56)', fontsize=10)

    ax.annotate('', xy=(1, 0.55), xytext=(0, 0.62),
                arrowprops=dict(arrowstyle='<->', color='gray', lw=1.2))
    ax.text(0.5, 0.60, f'gap = 0.096', ha='center', fontsize=8, color='gray')

    ax.annotate('', xy=(2, 0.35), xytext=(1, 0.54),
                arrowprops=dict(arrowstyle='<->', color=CB_RED, lw=1.2))
    ax.text(1.5, 0.45, f'regret = 0.264', ha='center', fontsize=8, color=CB_RED)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.065, f'{val:.3f}',
                ha='center', fontsize=8, fontweight='bold')

    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'fig4_adaptive_control.pdf'), dpi=300, bbox_inches='tight')
    fig.savefig(os.path.join(FIGDIR, 'fig4_adaptive_control.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print('  fig4_adaptive_control: saved')


def fig5_cross_level():
    """Cross-level replication ladder."""
    findings = [
        'Complementarity',
        'Attack timing',
        'Interference',
        'Seq > primitive',
        'Order effects',
        'Adaptive ctrl',
    ]
    levels = {
        'Simulator':        [1, 1, 0.5, 1, 1, 0.3],
        'LLM execution':    [1, 1, 0.5, 0, 0, 0],
        'Curated evidence': [0, 0, 0,   0, 0, 0],
    }

    fig, ax = plt.subplots(figsize=(5.5, 3.5))
    y = np.arange(len(findings))
    height = 0.25
    colors_map = {
        'Simulator': CB_BLUE,
        'LLM execution': CB_ORANGE,
        'Curated evidence': CB_PURPLE,
    }

    for i, (level_name, vals) in enumerate(levels.items()):
        offset = (i - 1) * height
        bars = ax.barh(y + offset, vals, height, label=level_name,
                       color=colors_map[level_name], edgecolor='white', linewidth=0.5)

    ax.set_yticks(y)
    ax.set_yticklabels(findings, fontsize=9)
    ax.set_xlim(0, 1.3)
    ax.set_xticks([0, 0.5, 1.0])
    ax.set_xticklabels(['Not supported', 'Directional', 'Supported'], fontsize=8)
    ax.legend(fontsize=8, loc='lower right')
    ax.set_title('Cross-Level Replication Status', fontsize=10)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, 'fig5_cross_level.pdf'), dpi=300, bbox_inches='tight')
    fig.savefig(os.path.join(FIGDIR, 'fig5_cross_level.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print('  fig5_cross_level: saved')


if __name__ == '__main__':
    print('Generating figures...')
    fig2_complementarity_matrix()
    fig3_attack_timing()
    fig4_adaptive_control()
    fig5_cross_level()
    print('Done.')
