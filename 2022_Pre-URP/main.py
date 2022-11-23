import os
import sys
import time
from pathlib import Path

import lda as lda
import numpy as np
import logging
import mne
import warnings

import scipy
import sklearn.decomposition
from lda import LDA
from mne.channels import read_layout
from mne.decoding import CSP
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import cross_val_score, ShuffleSplit
from sklearn.pipeline import Pipeline

if not os.path.isdir("./Plot"):
    os.mkdir("./Plot")

warnings.simplefilter("ignore", DeprecationWarning)
logging.basicConfig(
    format="%(asctime)s - %(levelname)s — %(funcName)s:%(lineno)d ——— %(message)s",
    datefmt="%d.%m.%Y-%H:%M:%S",
    level=logging.DEBUG,
    handlers=[logging.FileHandler("logs.txt", "w", encoding="UTF-8")],
)

logger = logging.getLogger()


def load_file(filename):
    return os.path.join(os.path.dirname(__file__), filename)


DATAFOLDER_NAME = "BCICIV_2a_gdf"
EXT = ".gdf"
# noinspection PyTypeChecker
gdf_files = [
    os.path.join(load_file(DATAFOLDER_NAME), _)
    for _ in os.listdir(load_file(DATAFOLDER_NAME))
    if _.endswith(EXT)
]
print(gdf_files)

file = gdf_files[3]

for file in gdf_files:
    try:
        raw = mne.io.read_raw_gdf(
            file, exclude=("EOG-left", "EOG-central", "EOG-right"), preload=True
        )
        raw.load_data()
        raw = raw.notch_filter(60)
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
        raw.rename_channels(ch)
        montage = mne.channels.make_standard_montage("standard_1005")

        events, event_id = mne.events_from_annotations(
            raw, event_id={"769": 1, "770": 2, "771": 3, "772": 4}
        )
        epochs = mne.Epochs(
            raw,
            events,
            event_id=event_id,
            preload=True,
            tmin=1,
            tmax=5.5,
            baseline=(1, 1.5),
        )
        epochs.set_montage(montage)
        epochs_train = epochs.copy()
        labels = epochs.events[:, -1] - 2
        epochs.load_data()
        # epochs["769"].plot_psd_topomap().savefig("769.png")
        # epochs["770"].plot_psd_topomap().savefig("770.png")
        # epochs["771"].plot_psd_topomap().savefig("771.png")
        # epochs["772"].plot_psd_topomap().savefig("772.png")

        scores = []
        epochs_data = epochs.get_data()
        epochs_data_train = epochs_train.get_data()
        cv = ShuffleSplit(10, test_size=0.2, random_state=42)
        cv_split = cv.split(epochs_data_train)

        lda = LinearDiscriminantAnalysis()
        csp = CSP(n_components=4, reg=None, log=True, norm_trace=False)

        clf = Pipeline([("CSP", csp), ("LDA", lda)])
        scores = cross_val_score(clf, epochs_data_train, labels, cv=cv)

        # Printing the results
        class_balance = np.mean(labels == labels[0])
        class_balance = max(class_balance, 1.0 - class_balance)
        print(
            "Classification accuracy: %f / Chance level: %f"
            % (np.mean(scores), class_balance)
        )

        # plot CSP patterns estimated on full data for visualization
        csp.fit_transform(epochs_data, labels)

        csp.plot_patterns(
            epochs.info, ch_type="eeg", units="Patterns (AU)", size=1.5
        ).savefig(f"./Plot/{Path(file).stem}_csp.png")
        print(file)
        print("saved")

        # logging
        raw_info = raw.info
        raw_ch_names = raw.ch_names
        logger.info(raw_info)
        logger.info(raw_ch_names)
        logger.info(epochs.info)
        logger.info("\n")
    except Exception as e:
        print(e)
