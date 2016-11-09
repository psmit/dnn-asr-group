First
=====

Run always first

    . ./path.sh 

To make sure that the binaries are loaded in your path

Data
====

All data used comes directly from the free (Creative Commons BY-NC-ND 3.0) Tedlium V2 corpus http://www-lium.univ-lemans.fr/en/content/ted-lium-corpus

Data set division
=================

The tedlium data is split in a train, dev and test set. For the scope of this project the full dataset is probably to big, so the features have (for now) only been extracted for a random 20h training subset and the complete dev and evaluation sets


Features
========

For all directories (except the full train set), two types of features have been pre-extracted. 13-dimensional mfcc-features have been extracted with:

    for dataset in 'train_20h' 'dev' 'test'; do
        extract-segments scp,p:${dataset}/wav.scp ${dataset}/segments ark:- | compute-mfcc-feats --use-energy=false ark:- ark:- | copy-feats --compress=true ark:- ark,scp:/work/courses/T/S/89/5150/general/data/tedlium/data/${dataset}_mfcc.ark,${dataset}/mfcc.scp
        compute-cmvn-stats --spk2utt=ark:${dataset}/spk2utt scp:${dataset}/mfcc.scp ark,scp:/work/courses/T/S/89/5150/general/data/tedlium/data/cmvn_${dataset}_mfcc.ark,${dataset}/mfcc_cmvn.scp
    done

Higher dimensional mfcc-features (which are similar in functionality to filterbanks) are extracted with:

    for dataset in 'train_20h' 'dev' 'test'; do
        extract-segments scp,p:${dataset}/wav.scp ${dataset}/segments ark:- | compute-mfcc-feats --use-energy=false --num-mel-bins=40 --num-ceps=40 --low-freq=20 --high-freq=-400 ark:- ark:- | copy-feats --compress=true ark:- ark,scp:/work/courses/T/S/89/5150/general/data/tedlium/data/${dataset}_hires.ark,${dataset}/hires.scp
        compute-cmvn-stats --spk2utt=ark:${dataset}/spk2utt scp:${dataset}/hires.scp ark,scp:/work/courses/T/S/89/5150/general/data/tedlium/data/cmvn_${dataset}_hires.ark,${dataset}/hires_cmvn.scp
    done

You don't have to run this commands yourself but they are useful when you need to describe what features you used. You can run `extract-segments` without parameters to find out what the options mean.

Training
========

Make a subset of the desired size. There are appr. 440 utterances / hour, so the following command creates a train subset of 1hour:

    utils/subset_data_dir.sh train_20h 440 train_1h

If you need dataset bigger then 20 hours let me know and I'll run the feature extraction for you.

X-data
------

This command generates a input matrix for each file

    apply-cmvn --utt2spk=ark:train_1h/utt2spk scp:train_1h/mfcc_cmvn.scp scp:train_1h/mfcc.scp ark:- | add-deltas ark:- ark,t:-

This command applies means and variance normalization for each speaker and then adds delta features. If you want higher-dimensional features change mfcc.scp to hires.scp. If you don't want normalization done the command is simply:

    add-deltas ark:train_1h/mfcc.scp ark,t:-

Also no deltas?

    copy-feats ark:train_1h/mfcc.scp ark,t:-

Use the same feature command when doing recognition, just change the dataset (`train_1h` -> `dev`)

Y-data
------

    ali-to-pdf mono_ali/final.mdl "ark:gunzip -c mono_ali/ali.*.gz|" ark,t:- | utils/filter_scp.pl train_20h/mfcc.scp

Change `train_20h` to the actual train subset you want the labels of


Recognition
===========

For each file a matrix needs to be output, with the log-likelihood of each pdf in the columns for each feature in the rows. See an example format from the gmm code:

    apply-cmvn --utt2spk=ark:dev/utt2spk scp:dev/mfcc_cmvn.scp scp:dev/mfcc.scp ark:- | add-deltas ark:- ark:- | gmm-compute-likes mono/final.mdl ark:- ark,t:- | less

This result can be fed to the latgen-faster-mapped command:

    recog_dir=gmm_recog
    mkdir $recog_dir
    apply-cmvn --utt2spk=ark:dev/utt2spk scp:dev/mfcc_cmvn.scp scp:dev/mfcc.scp ark:- | add-deltas ark:- ark:- | gmm-compute-likes mono/final.mdl ark:- ark:- | latgen-faster-mapped-parallel --num-threads=4 --num-threads=4 --beam=13.0 --lattice-beam=10.0 --word-symbol-table=mono/graph/words.txt mono/final.mdl mono/graph/HCLG.fst ark:- "ark:| gzip -c > $recog_dir/lat.1.gz"

After that run

    steps/score_kaldi.sh dev mono/graph $recog_dir

and the best result can be found in `$recog_dir/best_wer`


Smaller devset
--------------

The dev (and eval set) are actually quite big. It is totally valid to take a subset of it to get results faster. I suggest using:

    utils/subset_data_dir.sh --per-spk dev 2 dev_2

which creates a dev_2 directory with only 2 utterances / dev speaker. Now in all recognition commands you can use `dev_2` instead of `dev`
