
# **Extension of the Library:**  
https://github.com/stevegal/solis_control

# **solis_control**

**solis control** pyscript for Home Assistant.

**NOTE:** You need the [pyscript plugin](https://hacs-pyscript.readthedocs.io/en/latest/) installed.  
This script should be placed into the `pyscript` folder on your install. Once it's there, just call it as described below.

The pyscript requires the following settings to be added to the configuration, either from the UI or in your global configuration yaml:

```yaml
pyscript:
  allow_all_imports: true
  hass_is_global: true
```

## **Config**

Call the service like this:

```yaml
service: pyscript.solis_control
data:
  days:
    - chargeCurrent: "50"
      dischargeCurrent: "50"
      chargeStartTime: "03:00"
      chargeEndTime: "04:30"
      dischargeStartTime: "00:00"
      dischargeEndTime: "00:00"
    - chargeCurrent: "50"
      dischargeCurrent: "50"
      chargeStartTime: "00:00"
      chargeEndTime: "00:00"
      dischargeStartTime: "00:00"
      dischargeEndTime: "00:00"
    - chargeCurrent: "50"
      dischargeCurrent: "50"
      chargeStartTime: "00:00"
      chargeEndTime: "00:00"
      dischargeStartTime: "00:00"
      dischargeEndTime: "00:00"
  config:
    secret: API_SECRET
    key_id: API_KEY
    username: USERNAME
    password: PASSWORD
    plantId: PLANT_ID
    inverterSn: YOUR INVERTER SN
```

**Note:** Configuration items like `key_id`, `secret`, `plantId`, and `password` must be defined as strings, so wrap them in `" "` to ensure correctness.

To find the plantId, please follow the excellent instructions provided in [solis-sensor](https://github.com/hultenvp/solis-sensor).
