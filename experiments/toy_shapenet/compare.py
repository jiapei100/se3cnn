# pylint: disable=C,R
# takes m7.py m8.py m9.py
# takes (train_normal, val_normal), (train_perturbed, val_normal) ....

# train each N times with each (train,eval) pair
#
# output all data to make graphs

import os
from se3_cnn.train.train import train
import argparse
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--number_of_epochs", type=int, required=True)

parser.add_argument("--train_data_path", type=str, nargs="+", required=True)
parser.add_argument("--train_csv_path", type=str, nargs="+", required=True)

parser.add_argument("--eval_data_path", type=str, nargs="*", required=True)
parser.add_argument("--eval_csv_path", type=str, nargs="*", required=True)
parser.add_argument("--eval_each", type=int, default=1)

parser.add_argument("--gpu", type=int, default=0)
parser.add_argument("--log_dir", type=str, required=True)
parser.add_argument("--model_path", type=str, nargs="+", required=True)
parser.add_argument("--repeat", type=int, required=True)

main_args = parser.parse_args()

try:
    os.mkdir(main_args.log_dir)
except OSError:
    pass

class Arguments:
    def __init__(self):
        self.number_of_epochs = None
        self.start_epoch = None
        self.eval_each = None
        self.gpu = None
        self.eval_data_path = None
        self.eval_csv_path = None
        self.restore_path = None
        self.model_path = None
        self.train_data_path = None
        self.train_csv_path = None
        self.log_dir = None

args = Arguments()

args.number_of_epochs = main_args.number_of_epochs
args.start_epoch = 0
args.eval_each = main_args.eval_each
args.gpu = main_args.gpu
#args.train_csv_path = "voxels/train_6x32.csv"
args.eval_data_path = main_args.eval_data_path #["voxels/val_normal/*.npy", "voxels/val_perturbed/*.npy"]
args.eval_csv_path = main_args.eval_csv_path # ["voxels/val_6x194.csv"] * 2
args.restore_path = None

assert len(main_args.train_csv_path) == len(main_args.train_data_path)
def remove_prefix(xs):
    p = os.path.commonprefix(xs)
    return [x.replace(p, "") for x in xs]

train_names = [(x + y).replace("/", "_").replace("*", "x") for x, y in
zip(remove_prefix([os.path.splitext(x)[0] for x in main_args.train_csv_path]),
remove_prefix(main_args.train_data_path))]

print(train_names)

xxx = []
yyy = []
for model in main_args.model_path:
    args.model_path = model

    name = os.path.splitext(os.path.basename(model))[0]
    model_dir = os.path.join(main_args.log_dir, name)
    try:
        os.mkdir(model_dir)
    except OSError:
        pass

    xx = []
    yy = []
    for i in range(main_args.repeat):
        x = []
        y = []
        for train_csv_path, train_data_path, train_name in zip(main_args.train_csv_path, main_args.train_data_path, train_names):
            args.train_csv_path = train_csv_path
            args.train_data_path = train_data_path

            args.log_dir = os.path.join(model_dir, "{}_{}".format(train_name, i))
            train(args)

            x.append(np.load(os.path.join(args.log_dir, "statistics_train.npy")))
            y.append(np.load(os.path.join(args.log_dir, "statistics_eval.npy")))
        xx.append(x)
        yy.append(y)

    xx = np.array(xx) # [repeat, train_type,           row, column]
    yy = np.array(yy) # [repeat, train_type, val_type, row, column]

    np.save(os.path.join(model_dir, "statistics_train.npy"), xx)
    np.save(os.path.join(model_dir, "statistics_eval.npy"), yy)
    xxx.append(xx)
    yyy.append(yy)

xxx = np.array(xxx) # [model, repeat, train_type,           row, column]
yyy = np.array(yyy) # [model, repeat, train_type, val_type, row, column]

np.save(os.path.join(main_args.log_dir, "statistics_train.npy"), xxx)
np.save(os.path.join(main_args.log_dir, "statistics_eval.npy"), yyy)

eval_accuracies = np.mean(yyy, axis=1)[:, :, :, -1, 1] # [model, train_type, val_type]
eval_accuracies_std = np.std(yyy, axis=1)[:, :, :, -1, 1] # [model, train_type, val_type]

for i, model in enumerate(main_args.model_path):
    name = os.path.splitext(os.path.basename(model))[0]

    print(name)
    for j, trian_name in enumerate(train_names):
        print(trian_name)
        print("Mean Accuracy = {}".format(eval_accuracies[i][j]))
        print("Std Accuracy = {}".format(eval_accuracies_std[i][j]))
