To run Bluenet in a virtual environment, follow these steps:

Install virtualenv:

```
pip3 install virtualenv
```

Create a virtual environment (python3.5+)

```
virtualenv -p python3.7 venv --no-site-packages
```

Enter the virtual environment

```
source venv/bin/activate
```

Install the dependencies (pick the ble one if you want to use ble)
(pip now defaults to the pip that belongs to the python version you selected)

```
pip install -r requirements.txt

OR

pip install -r requirements_ble.txt
```

Build the lib and add it to the dependencies (pick the ble one if you want to use ble)

```
./build.sh
```

Allow non-sudo use of the ble scanner

```
sudo setcap 'cap_net_raw,cap_net_admin+eip' venv/lib/python3.7/site-packages/bluepy/bluepy-helper
```