from fir_artifacts import artifacts as fir_artf
from fir_userinteraction.artifacts import DeviceName

# Triggered to install the artifact in the module
from fir_userinteraction.notifications import AutoNotifyMethod

fir_artf.install(DeviceName)

# Event hooks for different userinteraction models
METHODS_TO_REGISTER = (AutoNotifyMethod(),)

