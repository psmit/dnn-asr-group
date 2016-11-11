Using tensorflow on Aalto machines
==================================

You can log in to an Aalto-Linux machine (e.g. in Maarintalo) for GPU computing or you can use the following machines for CPU computations through ssh

    - brute.aalto.fi
    - force.aalto.fi
    
You can also reach desktop machines with GPU's in Maari, but you have to ssh to kosh.aalto.fi first and from there ssh to e.g.

    - zirkoni.aalto.fi
    - akaatti.aalto.fi
    - Complete list on https://inside.aalto.fi/pages/viewpage.action?pageId=38798383
    
In the desktop machines, first check with the command `who` that no-one is using the machine at the moment.

Tensorflow installation
-----------------------

You can use the same tensorflow installations for cpu and gpu. If no gpu is available the cpu will be used.

First, create a virtual environment:

    virtualenv --system-site-packages -p python2.7 env_tensorflow
    
And after that you can install Tensorflow 0.10 with this command:

    export TF_BINARY_URL=https://storage.googleapis.com/tensorflow/linux/gpu/tensorflow-0.10.0-cp27-none-linux_x86_64.whl
    env_tensorflow/bin/pip install --upgrade $TF_BINARY_URL
    
Note that you have to run still `. ./path.sh` to make sure that CuDNN is on your path.

You can try if everything works by running:

    env_tensorflow/bin/python -m tensorflow.models.image.mnist.convolutional
    
    
Keras installation
------------------

Simply run:

    env_tensorflow/bin/pip install keras
    

