# Installation Troubleshooting
Follow these steps to troubleshoot your OP25 installation.

python3 /home/dnaab/op25/op25/gr-op25_repeater/apps/rx.py --args "rtl" -N "LNA:47" -S 250000 -f 853.6375e6 -o 25000 -q 0 -T /home/dnaab/op25/op25/gr-op25_repeater/apps/trunk.tsv -V -2 2> stderr.2


## 1. Verify That OP25 Installed Correctly
Run the following inside /opt/op25:
    cd /home/dnaab/op25
    ls -l gr-op25_repeater/apps

## 2. Set the Python Path Manually
Python needs to know where OP25’s modules are. Try running:
    export PYTHONPATH=/home/dnaab/op25/build:$PYTHONPATH
    export PYTHONPATH=/home/dnaab/op25/op25/gr-op25_repeater/apps/tx:$PYTHONPATH
    echo 'export PYTHONPATH=/home/dnaab/op25/op25/gr-op25_repeater/apps/tx:$PYTHONPATH"' >> ~/.bashrc
    source ~/.bashrc

## 3. Try Starting OP25 again
Run the Command:    
    python3 /home/dnaab/op25/op25/gr-op25_repeater/apps/rx.py --args rtl -N LNA:47 -S 250000 -f 853.6375e6 -o 25000 -q 0 -T /opt/op25-project/trunk.tsv -V -2

## 4. If OP25 Started Correctly...
Run the command:
    If this works, add it permanently by adding this line to ~/.bashrc or /etc/environment:

# Reinstallation Instructions

## 1. Check for Python Dependencies
Run the command:
    sudo apt install -y python3-numpy python3-scipy python3-matplotlib python3-requests python3-zmq

## 2. Rebuild OP25
Run the commands:

    cd /home/dnaab
    mkdir -p build
    cd build
    cmake ..
    make -j$(nproc)
    sudo make install

## 3. Set Python Path
Run the commands:
    ''
    # SET THE INITIAL PATH
    export PYTHONPATH=/opt/op25/build:$PYTHONPATH
    # CHECK THE WORK
    echo $PYTHONPATH
    # MAKE PERSISTANT ON LOGIN
    echo 'export PYTHONPATH="/opt/op25/build:$PYTHONPATH"' >> ~/.bashrc
    source ~/.bashrc
    ''

## 4. Verify Python Can Find OP25
Run the command: 
    python3 -c "import op25_c4fm"
