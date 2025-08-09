# ---------------------------------------------------------------------------
#           Name: sh_math.py
#         Author: Anthony Beaucamp (aka Mohican)
#  Last Modified: 28/01/2011
#    Description: Useful Maths Routines (shared between client/server)
# ---------------------------------------------------------------------------


# -------------------------------
def lerp(ratio, min, max):
    # LERP of two numbers
    lerp = min + ((max - min) * ratio)
    return lerp
