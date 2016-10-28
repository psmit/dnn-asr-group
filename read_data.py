#!/usr/bin/env python3

from subprocess import Popen, PIPE, check_output

import numpy as np
import sys

if not "/work/courses/T/S/89/5150/general/bin/kaldi" in sys.path:
    sys.path.append("/work/courses/T/S/89/5150/general/bin/kaldi")
    
_ali_command = ("gunzip -c {dir}/ali.gz |"
                "ali-to-pdf {dir}/final.mdl ark:- ark,t:-")

_cached_alignments = None


def y_dim(alidir="mono_ali"):
    return int(
        check_output("hmm-info {dir}/final.mdl | grep 'number of pdfs'".format(dir=alidir), shell=True).split()[3])


def x_dim(set="train_20h", type="mfcc", cmvn=True, deltas=True):
    feat_command = _build_feature_command(set, type, cmvn, deltas)
    return int(check_output(feat_command + "| feat-to-dim ark:- -", shell=True).strip())


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


def _build_feature_command(set="train_20h", type="mfcc", cmvn=True, deltas=True):
    input = "scp:{set}/{type}.scp".format(set=set, type=type)
    utt2spk = "ark:{set}/utt2spk".format(set=set)
    cmvnin = "scp:{set}/{type}_cmvn.scp".format(set=set, type=type)

    commands = []
    if not cmvn and not deltas:
        commands.append("copy-feats {input} ark,t:-".format(input=input))
    else:
        if cmvn:
            commands.append(
                "apply-cmvn --utt2spk={utt2spk} {cmvn} {input} {output}".format(utt2spk=utt2spk,
                                                                                cmvn=cmvnin,
                                                                                input=input,
                                                                                output="ark:-" if deltas else "ark,t:-"))
            input = "ark:-"
        if deltas:
            commands.append("add-deltas {input} ark,t:-".format(input=input))

    return " | ".join(commands)


def read_features(set="train_20h", type="mfcc", cmvn=True, deltas=True):
    feat_command = _build_feature_command(set, type, cmvn, deltas)
    print(feat_command, file=sys.stderr)
    with Popen(feat_command, shell=True, stdout=PIPE) as features:
        yield from _read_features(features.stdout)


def read_joint_feat_alignment(alidir="mono_ali", set="train_20h", type="mfcc", cmvn=True, deltas=True):
    global _cached_alignments
    if _cached_alignments is None:
        _cached_alignments = {k: v for k, v in
                              _read_alignments(check_output(_ali_command.format(dir=alidir), shell=True).splitlines())}

    for key, val in read_features(set, type, cmvn, deltas):
        if key not in _cached_alignments:
            print("No alignment for {}".format(key), file=sys.stderr)
            continue

        assert len(val) == len(_cached_alignments[key])
        yield key, val, _cached_alignments[key]
