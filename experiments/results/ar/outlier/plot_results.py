import torch
import pickle as pkl
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("-cv_list", nargs="+",  default=[0, 1, 2, 3, 4],
                    help="The list of experiment cv identifiers to plot", type=int)
args = parser.parse_args()
cv_list = args.cv_list
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
plt.rc('text', usetex=True)
params = {'text.latex.preamble': r'\usepackage{amsmath}'}
plt.rcParams.update(params)
test_size = 2000
n_outliers = int(test_size/2)
metrics = np.zeros((4, test_size, len(cv_list)))
n_inspected = [n for n in range(test_size)]
load_dir = Path.cwd() / "experiments/results/ar/outlier"

for cv in cv_list:
    with open(load_dir/f'true_cv{cv}.pkl', 'rb') as f:
        true_reps = pkl.load(f)
    with open(load_dir/f'simplex_cv{cv}.pkl', 'rb') as f:
        simplex_reps = pkl.load(f)
    with open(load_dir/f'knn_dist_cv{cv}.pkl', 'rb') as f:
        knn_dist_reps = pkl.load(f)
    with open(load_dir/f'knn_uniform_cv{cv}.pkl', 'rb') as f:
        knn_uniform_reps = pkl.load(f)

    simplex_residuals = torch.from_numpy(((true_reps - simplex_reps) ** 2).mean(axis=-1))
    knn_dist_residuals = torch.from_numpy(((true_reps - knn_dist_reps) ** 2).mean(axis=-1))
    knn_uniform_residuals = torch.from_numpy(((true_reps - knn_uniform_reps) ** 2).mean(axis=-1))
    counts_simplex = []
    counts_nn_dist = []
    counts_nn_uniform = []
    counts_random = []
    random_perm = torch.randperm(test_size)
    for k in range(simplex_residuals.shape[0]):
        _, simplex_top_id = torch.topk(simplex_residuals, k)
        _, nn_dist_top_id = torch.topk(knn_dist_residuals, k)
        _, nn_uniform_top_id = torch.topk(knn_uniform_residuals, k)
        random_id = random_perm[:k]
        count_simplex = torch.count_nonzero(simplex_top_id > n_outliers-1).item()
        count_nn_dist = torch.count_nonzero(nn_dist_top_id > n_outliers-1).item()
        count_nn_uniform = torch.count_nonzero(nn_uniform_top_id > n_outliers-1).item()
        count_random = torch.count_nonzero(random_id > n_outliers-1).item()
        counts_simplex.append(count_simplex)
        counts_nn_dist.append(count_nn_dist)
        counts_nn_uniform.append(count_nn_uniform)
        counts_random.append(count_random)
    metrics[0, :, cv] = counts_simplex
    metrics[1, :, cv] = counts_nn_dist
    metrics[2, :, cv] = counts_nn_uniform
    metrics[3, :, cv] = counts_random


counts_ideal = [n if n < n_outliers else n_outliers for n in range(test_size)]
sns.set()
sns.set_style("white")
sns.set_palette("colorblind")
plt.plot(n_inspected, metrics[0].mean(axis=-1), '-', label='SimplEx')
plt.fill_between(n_inspected, metrics[0].mean(axis=-1) - metrics[0].std(axis=-1),
                 metrics[0].mean(axis=-1) + metrics[0].std(axis=-1), alpha=0.3)
plt.plot(n_inspected, metrics[1].mean(axis=-1), ':', label='3NN Distance')
plt.fill_between(n_inspected, metrics[1].mean(axis=-1) - metrics[1].std(axis=-1),
                 metrics[1].mean(axis=-1) + metrics[1].std(axis=-1), alpha=0.3)
plt.plot(n_inspected, metrics[2].mean(axis=-1), '--', label='3NN Uniform')
plt.fill_between(n_inspected, metrics[2].mean(axis=-1) - metrics[2].std(axis=-1),
                 metrics[2].mean(axis=-1) + metrics[2].std(axis=-1), alpha=0.3)
plt.plot(n_inspected, metrics[3].mean(axis=-1), '-.', label='Random')
plt.fill_between(n_inspected, metrics[3].mean(axis=-1) - metrics[3].std(axis=-1),
                 metrics[3].mean(axis=-1) + metrics[3].std(axis=-1), alpha=0.3)
plt.plot(n_inspected, counts_ideal, label='Maximal')
plt.xlabel('Number of time series inspected')
plt.ylabel('Number of oscillating AR detected')
plt.legend()
plt.savefig(load_dir/'outlier.pdf', bbox_inches='tight')
