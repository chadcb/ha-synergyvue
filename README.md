# ha-synergyvue
Home Assistant Custom Component for SynergyVUE  

Clone/download custom_components/synergyvue folder to your Home Assistant custom_components folder.

Edit configuration.yaml file to add one sensor per student.

```yaml
# One sensor per student
sensor:
  - platform: synergyvue
    username: student01
    password: password
    host: synergyvue_host
    
  - platform: synergyvue
    username: student02
    password: password
    host: synergyvue_host
```
