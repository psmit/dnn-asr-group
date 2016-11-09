import numpy as np
import read_data

data = list(read_data.read_joint_feat_alignment(alidir="mono_ali", set="train_20h", type="mfcc", cmvn=True, deltas=True))

#Here all numpy arrays for each utterance are simply concatenated. If you are training e.g. a RNN this might not be what you want....
X_data = np.concatenate(tuple(x[1] for x in data))
y_data = np.concatenate(tuple(x[2] for x in data))

#Remove original numpy matrices to save memory
del data


print(X_data.shape)
print(y_data.shape)

# Now you can train (and save) your model