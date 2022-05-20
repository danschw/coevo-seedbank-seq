from __future__ import division
import numpy
import sys
from math import fabs
import glob, os, sys, re
import config
import utils
import parse_file
import pickle
import pandas
import scipy

import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from matplotlib.patches import Ellipse
import matplotlib.transforms as transforms
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

from sklearn.metrics import pairwise_distances
from skbio.stats.ordination import pcoa
import scipy.stats as stats

numpy.random.seed(123456789)

iter =10000

ks_path = "%sks_dist.pickle" % (config.data_directory)
measure_path = "%smeasure_dist.pickle" % (config.data_directory)

gene_intersection = utils.get_gene_intersection()
phage_or_host_type = 'host'
subpop_type = 'revived_total'
transfers = numpy.asarray(utils.transfers)

measures = ['max_f', 'delta_f', 'log_ratio']

def make_measure_dict():

    measure_dict = {}

    for seed_bank_type in utils.seed_bank_types:

        measure_dict[seed_bank_type] = {}

        for phage_treatment_type in utils.phage_treatment_types:

            measure_dict[seed_bank_type][phage_treatment_type] = {}
            measure_dict[seed_bank_type][phage_treatment_type]['log_ratio'] = []
            measure_dict[seed_bank_type][phage_treatment_type]['delta_f'] = []
            measure_dict[seed_bank_type][phage_treatment_type]['f_t'] = []

            max_freqs_all = []
            log_ratio_freqs_all = []
            delta_f_all = []
            f_t_all = []

            exists_all = False
            for replicate in utils.replicates:
                exists, annotated_mapgd_dict = utils.load_annotated_breseq(phage_or_host_type, seed_bank_type, phage_treatment_type, subpop_type, replicate)

                if exists == False:
                    continue

                else:
                    exists_all = True

                replicate_name = '%s_%s_%d' % (seed_bank_type, phage_treatment_type, replicate)

                for position, position_dict in annotated_mapgd_dict.items():

                    gene = position_dict['gene']

                    if (gene == 'intergenic') or (gene == 'repeat'):
                        continue

                    if phage_or_host_type == 'host':
                        # ignore genes that aren't in both strains
                        if gene not in gene_intersection:
                            continue

                    if (position_dict['annotation'] == 'synonymous') or (position_dict['annotation'] == 'noncoding'):
                        continue

                    frequency_trajectory = position_dict['frequency_trajectory']

                    if sum(frequency_trajectory>0) < utils.min_n_non_zero_freqs:
                        continue

                    frequency_trajectory_idx = (frequency_trajectory>0) & (frequency_trajectory<1)
                    transfers_i = transfers[frequency_trajectory_idx]
                    frequency_trajectory = frequency_trajectory[frequency_trajectory_idx]

                    if len(frequency_trajectory) == 0:
                        continue

                    delta_f_trajectory = numpy.absolute(frequency_trajectory[1:] - frequency_trajectory[:-1]) / (transfers_i[1:] - transfers_i[:-1])
                    log_ratio_frequency_trajectory = numpy.log10(frequency_trajectory[1:]/frequency_trajectory[:-1])

                    delta_f_trajectory = delta_f_trajectory[numpy.logical_not(numpy.isnan(delta_f_trajectory))]
                    log_ratio_frequency_trajectory = log_ratio_frequency_trajectory[numpy.logical_not(numpy.isnan(log_ratio_frequency_trajectory))]


                    # delta_f_trajectory.tolist()

                    if max(frequency_trajectory) > 0:
                        max_freqs_all.append(max(frequency_trajectory))
                    delta_f_all.extend(delta_f_trajectory.tolist())
                    log_ratio_freqs_all.extend(log_ratio_frequency_trajectory.tolist())

                    # pair with log_ratio
                    f_t_all.extend(frequency_trajectory[:-1].tolist())

            measure_dict[seed_bank_type][phage_treatment_type]['max_f'] = numpy.asarray(max_freqs_all)
            measure_dict[seed_bank_type][phage_treatment_type]['delta_f'] = numpy.asarray(delta_f_all)
            measure_dict[seed_bank_type][phage_treatment_type]['log_ratio'] = 10**numpy.asarray(log_ratio_freqs_all)
            measure_dict[seed_bank_type][phage_treatment_type]['f_t'] = numpy.asarray(f_t_all)

    with open(measure_path, 'wb') as handle:
        pickle.dump(measure_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)


def load_measure_dict():

    with open(measure_path, 'rb') as handle:
        measure_dict = pickle.load(handle)
    return measure_dict



def make_ks_dist_dict():

    measure_dict = load_measure_dict()

    ks_dist_dict = {}

    for measure in measures:

        ks_dist_dict[measure] = {}

        for seed_bank_type in utils.seed_bank_types:

            no_phage = measure_dict[seed_bank_type]['noPhage'][measure]
            phage = measure_dict[seed_bank_type]['SPO1'][measure]

            no_phage = numpy.log10(no_phage)
            phage = numpy.log10(phage)
            #print(no_phage)
            D, p = scipy.stats.ks_2samp(no_phage, phage)

            measure_array_merged = numpy.concatenate((no_phage, phage))

            D_null_all = []
            for i in range(iter):
                numpy.random.shuffle(measure_array_merged)

                no_phage_null = measure_array_merged[:len(no_phage)]
                phage_null = measure_array_merged[len(no_phage):]

                D_null, p_null = scipy.stats.ks_2samp(no_phage_null, phage_null)
                D_null_all.append(D_null)

            D_null_all = numpy.asarray(D_null_all)
            D_null_all = numpy.sort(D_null_all)

            p_perm = sum(D_null_all > D)/iter

            lower_ci = D_null_all[int(iter*0.025)]
            upper_ci = D_null_all[int(iter*0.975)]

            ks_dist_dict[measure][seed_bank_type] = {}
            ks_dist_dict[measure][seed_bank_type]['D'] = D
            ks_dist_dict[measure][seed_bank_type]['p'] = p_perm
            ks_dist_dict[measure][seed_bank_type]['null_mean'] = numpy.mean(D_null_all)
            ks_dist_dict[measure][seed_bank_type]['null_median'] = numpy.median(D_null_all)
            ks_dist_dict[measure][seed_bank_type]['lower_ci'] = lower_ci
            ks_dist_dict[measure][seed_bank_type]['upper_ci'] = upper_ci

    with open(ks_path, 'wb') as handle:
        pickle.dump(ks_dist_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)



def load_ks_dict():

    with open(ks_path, 'rb') as handle:
        ks_dist_dict = pickle.load(handle)
    return ks_dist_dict



ylim_inset_dict = {'max_f': [-0.005, 0.09 ],
            'delta_f': [-0.005, 0.06],
            'log_ratio': [-0.005, 0.05]}



def plot_ks_dist():

    measure_dict = load_measure_dict()
    ks_dist_dict = load_ks_dict()

    fig = plt.figure(figsize = (5, 12)) #
    fig.subplots_adjust(bottom= 0.15,  wspace=0.25)


    import matplotlib as mpl
    mpl.rcParams['xtick.labelsize'] = 6
    mpl.rcParams['ytick.labelsize'] = 7

    x_axis_labels = ['Maximum observed allele frequency, ' + r'$f_{max}$', 'Absolute change in allele frequencies per-transfer, ' + r'$|\Delta f| / \Delta t$', 'Ratio of allele frequency changes, ' + r'$f(t+\delta t)/f(t)$']
    y_axis_labels = ['Fraction ' + r'$\geq f_{max}$', 'Fraction ' + r'$\geq |\Delta f| / \Delta t$', 'Fraction ' + r'$\geq f(t+\delta t)/f(t)$']
    for measure_idx, measure in enumerate(measures):

        ax = plt.subplot2grid((3, 1), (measure_idx, 0), colspan=1)

        for seed_bank_type in utils.seed_bank_types:
            for phage_treatment_type in utils.phage_treatment_types:

                 log_ratio_array_sort = numpy.sort(measure_dict[seed_bank_type][phage_treatment_type][measure])
                 cdf = 1-numpy.arange(len(log_ratio_array_sort))/float(len(log_ratio_array_sort))

                 label = utils.seed_bank_types_format_dict[seed_bank_type] + ', ' + utils.phage_treatment_types_format_dict[phage_treatment_type]

                 ax.plot(log_ratio_array_sort, cdf, c =utils.color_dict[seed_bank_type], ls=utils.line_dict[phage_treatment_type], label=label, lw=2, alpha=1)

        #ax.set_xlabel('' , fontsize = 12)
        #ax.set_ylabel('PCo 2 (' + str(round(df_pcoa.proportion_explained[1]*100, 1)) + '%)' , fontsize = 12)

        if measure_idx == 0:
            ax.legend(loc="upper right", fontsize=6)

        if measure == 'log_ratio':
            ax.set_xlim(10**-2, 10**4)

        if measure == 'delta_f':
            ax.set_xlim(10**-2.3, 0.3)

        if measure == 'max_f':
            ax.set_xlim(0.04, 1.1)

        #ax.tick_params(labelsize=10)
        #ax.tick_params(axis='both', which='major', pad=1)

        #ax.yaxis.set_tick_params(labelsize=7)
        ax.set_xlabel(x_axis_labels[measure_idx], fontsize = 10)
        ax.set_ylabel(y_axis_labels[measure_idx], fontsize = 10)

        ax.set_xscale('log', basex=10)
        ax.set_yscale('log', basey=10)

        # inset axis
        ins_ks = inset_axes(ax, width="100%", height="100%", loc='lower right', bbox_to_anchor=(0.14,0.07,0.4,0.38), bbox_transform=ax.transAxes)

        for seed_bank_type_idx, seed_bank_type in enumerate(utils.seed_bank_types):

            D = ks_dist_dict[measure][seed_bank_type]['D']

            #marker_style = dict()

            ins_ks.plot(seed_bank_type_idx, D, markersize = 11, marker = 'o',  \
                linewidth=0.4,  alpha=1, color=utils.color_dict[seed_bank_type], zorder=2)


            print(ks_dist_dict[measure][seed_bank_type]['lower_ci'])
            print(ks_dist_dict[measure][seed_bank_type]['upper_ci'])

            delta = 0.05
            fill_between_x = numpy.asarray([seed_bank_type_idx-delta, seed_bank_type_idx+delta])
            fill_between_y_lower = numpy.asarray([ks_dist_dict[measure][seed_bank_type]['lower_ci'], ks_dist_dict[measure][seed_bank_type]['lower_ci']])
            fill_between_y_upper = numpy.asarray([ks_dist_dict[measure][seed_bank_type]['upper_ci'], ks_dist_dict[measure][seed_bank_type]['upper_ci']])

            ins_ks.fill_between(fill_between_x, y1=fill_between_y_lower, y2=fill_between_y_upper, color='grey')

        # finish the ins_ks fiddling
        ins_ks.tick_params(labelsize=4)
        ins_ks.tick_params(axis='both', which='major', pad=1)

        ins_ks.set_xlim([-0.5, 2.5])
        ins_ks.set_ylim(ylim_inset_dict[measure])

        ins_ks.set_xticks([0, 1, 2])

        ins_ks.set_xticklabels([utils.seed_bank_types_format_split_dict[s] for s in utils.seed_bank_types] )
        ins_ks.set_ylabel("KS distance b/w\nphage and no phage", fontsize=5)
        ins_ks.tick_params(axis='x', labelsize=5, length = 0)

        ins_ks.axhline(y=0, color='k', linestyle=':', alpha = 0.8, zorder=1)
        ins_ks.yaxis.set_tick_params(labelsize=4)


    fig_name = '%sfluctuation_survival.png' % (config.analysis_directory)
    fig.savefig(fig_name, bbox_inches = "tight", pad_inches = 0.4, dpi = 600)
    plt.close()


def plot_f_vs_f_ratio():

    measure_dict = load_measure_dict()

    fig = plt.figure(figsize = (12, 8)) #
    fig.subplots_adjust(bottom= 0.15,  wspace=0.25)

    import matplotlib as mpl
    mpl.rcParams['xtick.labelsize'] = 8
    mpl.rcParams['ytick.labelsize'] = 8

    slope_dict = {}

    for seed_bank_type_idx, seed_bank_type in enumerate(utils.seed_bank_types):
        slope_dict[seed_bank_type] = {}
        for phage_treatment_type_idx, phage_treatment_type in enumerate(utils.phage_treatment_types):

            slope_dict[seed_bank_type][phage_treatment_type] = {}

            ax = plt.subplot2grid((2, 3), (phage_treatment_type_idx, seed_bank_type_idx), colspan=1)

            x = numpy.asarray(measure_dict[seed_bank_type][phage_treatment_type]['f_t'])
            y = numpy.asarray(measure_dict[seed_bank_type][phage_treatment_type]['log_ratio'])

            x_log10 = numpy.log10(x)
            y_log10 = numpy.log10(y)

            slope, intercept, r_value, p_value, std_err = stats.linregress(x_log10, y_log10)

            slope_dict[seed_bank_type][phage_treatment_type]['slope'] = slope
            slope_dict[seed_bank_type][phage_treatment_type]['x_log10'] = x_log10
            slope_dict[seed_bank_type][phage_treatment_type]['y_log10'] = y_log10


            all_ = numpy.concatenate([x, y])
            xy = numpy.vstack([x, y])
            z = stats.gaussian_kde(xy)(xy)
            # Sort the points by density, so that the densest points are plotted last
            idx_ = z.argsort()
            x, y, z = x[idx_], y[idx_], z[idx_]
            ax.scatter(x, y, c=z, cmap=utils.seed_bank_type_cmap_dict[seed_bank_type], s=90, alpha=0.9, edgecolor='', zorder=1)
            ax.text(0.2,  0.25, r'$\beta_{1} =$' + str( round(slope, 3) ), fontsize=8, color='k', ha='center', va='center', transform=ax.transAxes  )


            x_range =  numpy.logspace(-3, max(x_log10), 10000, base=10.0)
            y_fit = (slope*numpy.log10(x_range) + intercept)

            ax.plot(x_range, 10**y_fit, c='k', lw=2.5, linestyle='--', zorder=2)
            ax.set_xscale('log', basex=10)
            ax.set_yscale('log', basey=10)


            if seed_bank_type_idx == 0:
                ax.set_ylabel('Ratio of allele frequency changes, ' + r'$f(t+\delta t)/f(t)$', fontsize = 8)
                ax.text(-0.3,  0.5, utils.phage_treatment_types_format_caps_dict[phage_treatment_type], fontsize=12, color='k', ha='center', va='center', fontweight='bold', rotation=90, transform=ax.transAxes  )

            if phage_treatment_type_idx == 0:
                ax.set_title(utils.seed_bank_types_format_dict[seed_bank_type], fontsize=12, fontweight='bold', color='k' )

            if phage_treatment_type_idx == 1:
                ax.set_xlabel('Allele frequency, ' + r'$f(t)$', fontsize = 10)


    fig_name = '%sf_vs_f_ratio.png' % (config.analysis_directory)
    fig.savefig(fig_name, bbox_inches = "tight", pad_inches = 0.4, dpi = 600)
    plt.close()


    # run slope difference test
    for seed_bank_type_idx, seed_bank_type in enumerate(utils.seed_bank_types):

        slope_1 = slope_dict[seed_bank_type]['noPhage']['slope']
        slope_2 = slope_dict[seed_bank_type]['SPO1']['slope']

        slope_delta = slope_2 - slope_1

        n_1 = len(slope_dict[seed_bank_type]['noPhage']['x_log10'])
        n_2 = len(slope_dict[seed_bank_type]['SPO1']['x_log10'])

        x = numpy.concatenate((slope_dict[seed_bank_type]['noPhage']['x_log10'], slope_dict[seed_bank_type]['SPO1']['x_log10']))
        y = numpy.concatenate((slope_dict[seed_bank_type]['noPhage']['y_log10'], slope_dict[seed_bank_type]['SPO1']['x_log10']))

        delta_slope_null_all = []
        for i in range(iter):

            numpy.random.shuffle(x)
            numpy.random.shuffle(y)

            x_1_null = x[:n_1]
            x_2_null = x[n_1:]

            y_1_null = y[:n_1]
            y_2_null = y[n_1:]

            slope_1_null, intercept_1_null, r_value_1_null, p_value_1_null, std_err_1_null = stats.linregress(x_1_null, y_1_null)
            slope_2_null, intercept_2_null, r_value_2_null, p_value_2_null, std_err_2_null = stats.linregress(x_2_null, y_2_null)

            delta_slope_null = slope_2_null - slope_1_null
            delta_slope_null_all.append(delta_slope_null)

        delta_slope_null_all = numpy.asarray(delta_slope_null_all)

        p = sum(delta_slope_null_all<slope_delta)/iter

        print(seed_bank_type, p)







plot_f_vs_f_ratio()
