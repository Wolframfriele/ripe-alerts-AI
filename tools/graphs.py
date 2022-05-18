"""This module contains code to plot various kinds of graphs"""
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from adtk.detector import LevelShiftAD
from adtk.data import validate_series
from adtk.visualization import plot


class MultiVariatePlot:
    def __init__(self, df) -> None:
        self.df = df
        self.pre_processed = False

    def calc_score(self, median, hops):
        if hops is None:
            return 0
        return abs(float(hops) - median)

    def normalize(self, min_score, max_score, score):
        if max_score-min_score == 0:
            return 0
        return (score-min_score) / (max_score-min_score)

    def pre_process_data(self):
        if not self.pre_processed:
            print("Pre-processing")
            unique_probes = self.df['probe_id'].unique()

            for idx, probe_id in enumerate(unique_probes):
                hops_series_probe = self.df[self.df['probe_id']
                                            == probe_id]['entry_rtt']
                median = hops_series_probe.median()
                scores = hops_series_probe.apply(
                    lambda min_rtt: self.calc_score(median, min_rtt))
                score_max = scores.max()
                score_min = scores.min()
                normalized_scores = scores.apply(
                    lambda score: self.normalize(score_min, score_max, score))
                self.df.loc[self.df['probe_id'] ==
                            probe_id, 'median_probe_hops'] = median
                self.df.loc[self.df['probe_id'] == probe_id,
                            'not_normalized_score'] = scores
                self.df.loc[self.df['probe_id'] == probe_id,
                            'normalized_score'] = normalized_scores
                self.df.loc[self.df['probe_id'] == probe_id,
                            'normalized_probe_id'] = int(idx)
            self.pre_processed = True

    def plot_dataset(self):
        self.pre_process_data()
        sns.set(rc={"figure.figsize": (24, 20)})
        sns.set_style("white")
        sns.scatterplot(data=self.df, x="created", y="normalized_probe_id",
                        hue="normalized_score", legend=False, palette="light:black")

    def plot_as(self, as_num=False, random_state=42):
        self.pre_process_data()
        if not as_num:
            as_num = self.df["entry_as"].sample(
                n=1, random_state=random_state).unique()[0]
        as_num = str(as_num)
        single_as_df = self.df[self.df['entry_as'] == as_num]

        sns.set(rc={"figure.figsize": (24, 10)})
        sns.set_style("white")
        sns.scatterplot(data=single_as_df, x="created", y="normalized_probe_id",
                        hue="normalized_score", legend=False, palette="light:black")
        plt.title(f'Multivariate Round Trip Time of probes in AS{as_num}', fontsize =20)
        plt.xlabel('Round Trip Time at Time (Darker dot means higher RTT)', fontsize = 15)
        plt.ylabel('Normalised Probe ID', fontsize = 15)


class ProbesPerAS:
    def __init__(self, df) -> None:
        self.df = df

    def plot(self, cap=10):
        probes_in_as = []
        unique_as_num = self.df['entry_as'].unique()

        for as_num in unique_as_num:
            single_as_df = self.df[self.df['entry_as'] == as_num]
            probes_in_as.append(len(single_as_df['probe_id'].unique()))

        unique_as_num = [x for y, x in sorted(
            zip(probes_in_as, unique_as_num), reverse=True)]
        probes_in_as.sort(reverse=True)
        sns.set(rc={"figure.figsize": (24, 10)})
        sns.barplot(x=unique_as_num[:10], y=probes_in_as[:cap])
        plt.title(f'Amount of probes that measure through neighboring AS', fontsize =20)
        plt.xlabel('Neighboring AS Numbers', fontsize = 15)
        plt.ylabel('Amount of Probes', fontsize = 15)


class AggregatedAnomalies:
    def __init__(self, df, aggregated) -> None:
        self.df = df
        self.aggregated = aggregated

    def plot(self, random_state=42, as_number=None) -> None:
        if not as_number:
            as_number = self.df["entry_as"].sample(n=1, random_state=random_state).unique()[0]
        sns.set(rc={"figure.figsize": (24, 10)})
        sns.set_style("white")
        sns.lineplot(data=self.aggregated[str(as_number)], palette="light:black")
        plt.title(f'Aggregated Anomalies in AS{as_number}', fontsize =20)
        plt.xlabel('Datetime', fontsize = 15)
        plt.ylabel('Aggregated Anomalies at Time', fontsize = 15)
        return as_number


class SingleProbe:

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df

    def plot(self, as_number, random_state=42, probe_id=None):
        if not probe_id:
            as_df = self.df[self.df["entry_as"] == str(as_number)]
            probe_id = as_df["probe_id"].sample(n=1, random_state=random_state).unique()[0]
            probe_as = self.df[self.df["probe_id"] == probe_id]["entry_as"].iloc[0]
        
        single_probe = self.df[self.df["probe_id"] == probe_id]
        single_probe.set_index('created', inplace=True)
        ts = single_probe['entry_rtt']
        ts = validate_series(ts)

        level_shift_ad = LevelShiftAD(c=10.0, side='positive', window=3)
        level_anomalies = level_shift_ad.fit_detect(ts,  return_list=True)
        plot(ts, anomaly=level_anomalies, anomaly_color='red', figsize=(24, 6), anomaly_alpha=0.6)
        plt.title(f'Round Trip Time at Entry Hop of probe: {probe_id} Through AS{probe_as}', fontsize =20)
        plt.xlabel('Datetime', fontsize = 15)
        plt.ylabel('RTT in ms', fontsize = 15)