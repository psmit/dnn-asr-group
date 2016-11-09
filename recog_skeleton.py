from read_data import read_features, write_pdfs


#You should load some model

for key, feats in read_features(set="dev_2", type="mfcc", cmvn=True, deltas=True):
    probs = model.predict(feats)

    write_pdfs(key, probs)
