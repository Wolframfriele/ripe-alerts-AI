"""This module contains code to plot various kinds of graphs"""
import pandas as pd
import seaborn as sns

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
            
            unique_probes = self.df['probe_id'].unique()

            for idx, probe_id in enumerate(unique_probes):
                hops_series_probe = self.df[self.df['probe_id'] == probe_id]['pre_entry_hop_min_rtt']
                median = hops_series_probe.median()
                scores = hops_series_probe.apply(lambda min_rtt: self.calc_score(median, min_rtt))
                score_max = scores.max()
                score_min = scores.min()
                normalized_scores = scores.apply(lambda score: self.normalize(score_min, score_max, score))
                self.df.loc[self.df['probe_id'] == probe_id, 'median_probe_hops'] = median
                self.df.loc[self.df['probe_id'] == probe_id, 'not_normalized_score'] = scores
                self.df.loc[self.df['probe_id'] == probe_id, 'normalized_score'] = normalized_scores
                self.df.loc[self.df['probe_id'] == probe_id, 'normalized_probe_id'] = int(idx)
    
    def plot_dataset(self):
        self.pre_process_data()
        sns.set(rc={"figure.figsize":(24, 20)})
        sns.set_style("white")
        sns.scatterplot(data=self.df, x="created", y="normalized_probe_id", hue="normalized_score",legend=False, palette="light:black")

    def plot_as(self, as_num=False, random_state=42):
        if not as_num:
            as_num = self.df["pre_entry_as"].sample(n=1, random_state=random_state).unique()[0]
        as_num = str(as_num)
        single_as_df = self.df[self.df['pre_entry_as'] == as_num]

        sns.set(rc={"figure.figsize":(24, 10)})
        sns.set_style("white")
        sns.scatterplot(data=single_as_df, x="created", y="normalized_probe_id", hue="normalized_score",legend=False, palette="light:black")


class ProbesPerAS:
    def __init__(self, df) -> None:
        self.df = df

    def plot(self, cap=10):
        probes_in_as = []
        unique_as_num = self.df['pre_entry_as'].unique()

        for as_num in unique_as_num:
            single_as_df = self.df[self.df['pre_entry_as'] == as_num]
            probes_in_as.append(len(single_as_df['probe_id'].unique()))

        unique_as_num = [x for y, x in sorted(zip(probes_in_as, unique_as_num), reverse=True)]
        probes_in_as.sort(reverse=True)
        sns.set(rc={"figure.figsize":(24, 10)})
        sns.barplot(x=unique_as_num[:10], y=probes_in_as[:cap])
