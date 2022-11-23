import mne as mne
import numpy as np
import scipy.io

# load train data to epoch
raw_t = mne.io.read_raw_gdf(
    "BCICIV_2a_gdf/A01T.gdf", exclude=("EOG-left", "EOG-central", "EOG-right")
)
raw_t.load_data()
raw_t = raw_t.notch_filter(60)
montage = mne.channels.make_standard_montage("standard_1005")
ch = {
    "EEG-Fz": "Fz",
    "EEG-0": "FC3",
    "EEG-1": "FC1",
    "EEG-2": "FCz",
    "EEG-3": "FC2",
    "EEG-4": "FC4",
    "EEG-5": "C5",
    "EEG-C3": "C3",
    "EEG-6": "C1",
    "EEG-Cz": "Cz",
    "EEG-7": "C2",
    "EEG-C4": "C4",
    "EEG-8": "C6",
    "EEG-9": "CP3",
    "EEG-10": "CP1",
    "EEG-11": "CPz",
    "EEG-12": "CP2",
    "EEG-13": "CP4",
    "EEG-14": "P1",
    "EEG-Pz": "Pz",
    "EEG-15": "P2",
    "EEG-16": "Oz",
}
raw_t.rename_channels(ch)
events, event_id = mne.events_from_annotations(
    raw_t, event_id={"769": 1, "770": 2, "771": 3, "772": 4}
)
epoch_t = mne.Epochs(raw_t, events, tmin=1, tmax=4, baseline=None, event_id=event_id)
epoch_t.set_montage(montage)
epoch_t.load_data()
epoch_t["769"].plot_psd_topomap()
epoch_t["769"].filter(8, 40).average().plot()
epoch_t["769"].plot_psd(fmin=8, fmax=40, picks=("C1", "C3", "C2", "C4")).savefig(
    "left.png"
)
