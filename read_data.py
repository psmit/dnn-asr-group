#!/usr/bin/env python3

from subprocess import Popen, PIPE, check_output

import numpy as np
import sys

#CONFIGURATION
_train_suffix = "_20h"
_feat_type = "mfcc"  # or hires

_feat_scp = "train{suffix}/{feat_type}.scp".format(suffix=_train_suffix, feat_type=_feat_type)
_cmvn_scp = "train{suffix}/{feat_type}_cmvn.scp".format(suffix=_train_suffix, feat_type=_feat_type)
_model = "mono/final.mdl"

_utt2spk = "train{suffix}/utt2spk".format(suffix=_train_suffix)

_ali_command = ("gunzip -c mono_ali/ali.gz |"#""gunzip -c mono_ali/ali.*.gz |"
               "ali-to-pdf mono_ali/final.mdl ark:- ark,t:- |"

               "utils/filter_scp.pl {feat_scp}").format(feat_scp=_feat_scp)

_feat_command = ("apply-cmvn --utt2spk=ark:{utt2spk} scp:{cmvn_scp} scp:{feat_scp} ark:- |"
                "add-deltas ark:- ark,t:-").format(feat_scp=_feat_scp, cmvn_scp=_cmvn_scp, utt2spk=_utt2spk)

_dev_feat_command = ("apply-cmvn --utt2spk=ark:{utt2spk} scp:{cmvn_scp} scp:{feat_scp} ark:- | add-deltas ark:- ark,t:-".format(
    utt2spk="dev/utt2spk", cmvn_scp="dev/mfcc_cmvn.scp", feat_scp="dev/mfcc.scp")

#END OF CONFIGURATION

_cached_alignments = None


def y_dim():
    return int(check_output("hmm-info {} | grep 'number of pdfs'".format(_model), shell=True).split()[3])


def x_dim():
    return int(check_output(_feat_command + "| feat-to-dim ark:- -", shell=True).strip())


def _read_alignments(file_in):
    for line in file_in:
        if len(line.strip()) == 0:
            continue
        key, labels = line.split(None, 1)
        yield key, np.asarray([int(i) for i in labels.split()])


def _read_features(file_in):
    while True:
        start_line = file_in.readline()
        if len(start_line) == 0:
            break
        feat_key, brace = start_line.split(None, 1)
        assert brace.strip() == b"["

        feats_list = []
        done = False
        dim = None
        while not done:
            values = file_in.readline().split()
            if values[-1] == b']':
                values = values[:-1]
                done = True

            if dim is None:
                dim = len(values)

            assert dim == len(values)
            feats_list.append(tuple(float(f) for f in values))
        yield feat_key, np.asarray(feats_list, dtype=np.float32)


def read_all():
    global _cached_alignments
    if _cached_alignments is None:
        _cached_alignments = {k: v for k,v in _read_alignments(check_output(_ali_command, shell=True).splitlines())}

    with Popen(_feat_command, shell=True, stdout=PIPE) as features:
        for key, val in _read_features(features.stdout):
            if key not in _cached_alignments:
                print("No alignment for {}".format(key), file=sys.stderr)
                continue

            assert len(val) == len(_cached_alignments[key])
            yield key, val, _cached_alignments[key]


def read_dev():
    with Popen(_dev_feat_command, shell=True, stdout=PIPE) as features:
        yield from _read_features(features.stdout)
