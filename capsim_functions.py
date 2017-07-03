#! /usr/bin/env python
#
#This file contains functions that are called by the capsim program.

from numpy import exp, log, interp, seterr, nan, sin, pi
from math import log10, floor

seterr(under = 'ignore', divide = 'raise', invalid = 'ignore')

def millquirk(e): 
    """Millington and Quirk model for tortuosity correction.
    e -- the porosity
    """

    return e**(4./3)

def boudreau(e):
    """Boudreau model for tortuosity correction.
    e -- the porosity
    """

    return e / (1 - log(e**2))

def notort(e):
    """No tortuosity correction.
    e -- the porosity
    """

    return e

def freundlich(C, Kf, N):
    """Freundlich isotherm for sorption onto cap materials.
    Kf -- the Freundlich K with units of (ug/kg) / (ug/L)**N
    N  -- 1/n = the Freundlich exponent (dimensionless)
    """
    
    try:    q      = Kf * C**(N-1)
    except: q      = 0.
    try:    dqdC   = N * Kf * C**(N-1)
    except: dqdC   = nan

    return q, dqdC

def langmuir(C, qmax, b):
    """Langmuir isotherm for sorption onto cap materials.
    qmax -- the maximum adsorption capacity with units of ug/kg
    b    -- the Langmuir adsorption constant with units of L/ug
    """

    q      = qmax * b / (1 + b * C)
    dqdC   = qmax * b / (1 + b * C)**2

    return q, dqdC

def kbllake(rhoair, rhowater, vwind, hlake, MW, llake, b = 18.9):
    """Benthic boundary layer mass transfer coefficient for lakes.  Returns the
    benthic boundary layer mass transfer coefficient "kbl" in cm/hr.  Based on
    empirical equation presented in Thibodeaux's book Chemodynamics, 
    2nd edition, 

    rhoair   -- density of air   (kg/L)
    rhowater -- density of water (kg/L)
    vwind    -- wind speed       (m/s)
    hlake    -- lake depth       (m)
    MW       -- molecular weight (g/mol)
    llake    -- lake fetch       (m)
    """

    if vwind < 6: Cd = 0.00166
    else:         Cd = 0.00237

    return (b * Cd * rhoair / rhowater * vwind**2 * hlake**2 / MW**0.5 / 
            llake * 100 * 3600)

def kblriver(vx, n, hriver, rh, nu, Dw):
    """Benthic boundary layer mass transfer coefficient for rivers.  Returns
    the boundary layer mass transfer coefficient "kbl" in cm/hr.  Based on
    empirical equation presented in Thibodeaux's book Chemodynamics, 2nd 
    edition, p. 266-267, which was derived for flat-bottom forced convection
    mass transfer measurements.

    vx     -- river velocity (m/s)
    n      -- Manning's n (-)
    hriver -- river depth (m)
    rh     -- hydraulic radius (m)
    nu     -- viscosity of water (m2/s)
    Dw     -- molecular diffusion coefficient (cm2/s)
    """

    return (0.114 * vx * n * (9.81 * hriver)**0.5 / rh**(2. / 3) / 
            (nu / Dw * 10**4)**(2./3) * 100 * 3600)

def tauwater(Q, doc, Kdoc, kdep, epsilon, dep_rho, dep_fraction, K, V, h, kevap, kdecay):

    """
    Q      -- Outflow rate
    V      -- Water boday volume
    h      -- Depth (m)
    kevap  -- Evaporation rate coefficient
    kdecay -- Decay rate coefficient
    """

    tau_1 = Q/V*(1+doc/10**6*10**Kdoc)+kevap/h+kdecay + kdep/h*epsilon
    for n in range(len(dep_fraction)):
        tau_1 = tau_1 + dep_fraction[n] * dep_rho * K[n] * kdep/h

    return (1./tau_1)

def consolidation(t, V0, k): 
    """Consolidation flowrate model.  "V0" is the initial velocity and "k" is 
    the "decay rate" over time.  Consolidation in the underlying sediment is 
    assumed to be of an exponential decay form:

        consolidation(t) = totalconsolidation * (1 - exp(-k * t))
            
    For our purposes this induces a flow Vcon in addition to the pre-
    existing Darcy velocity of:
            
        Vcon(t) = d consolidation(t) / dt
        Vcon(t) = totalconsolidation * k * exp(-k * t)
        Vcon(t) = V0 * exp(-k * t)
            
    Where:

        V0 = totalconsolidation * k
        k  = -ln(0.1) / t90
    """
    
    return V0 * exp(-k * t)

def tidal(t, Vtidal, ptidal):
    """ """
    
    return Vtidal * sin( t / ptidal * 2 * pi)

def HaydukLaudieDw(viscosity, MVol):
    """Method to estimate molecular diffusion coefficient in water from the
    viscosity of water 'viscosity' in centipoise and the molar volume 'MVol' in
    cm3/mol (from Hayduk and Laudie 1974)."""

    return (1.326*10**-4/viscosity**1.14/MVol**0.589)

def BakerKoc(logKow): 
    """Non-class specific correlation for estimating the organic carbon
    partition coefficient Koc from the octanol-water partition coefficient
    Kow (from Baker et al., Water Environment Research 69:136-145, 1997)."""

    return (0.903*logKow+0.09)

def PAHKoc(logKow):
    """PAH specific correlation for estimating Koc from Kow (Schwarzenbach citation)."""

    return (0.98*logKow-0.32)

def PCBKoc(logKow):
    """PCB specific correlation for estimating Koc from Koc (from MacKay 2006 
    Handbook for estimating properties of organic compounds)."""

    return (0.839*logKow+0.094)

def PAHKdoc(logKow):
    """PAH specific correlation for estimating Kdoc from Kow (from Burkhard 2000)."""

    return (1.18*logKow-1.56)

def PCBKdoc(logKow):
    """PCB specific correlation for estimating Kdoc from Koc (from Burkhard 2000)."""

    return (0.71*logKow-0.5)

def BurkhardKdoc(logKow):
    """Non-class specific correlation for estimating Kdoc from Kow 
    (from Burkhard 2000)."""

    return (logKow-1.09)

def h20viscosity(temp): 
    """Returns the approximate dynamic viscosity of water (centipoise)
    at a given temperature (Celsius)."""

    temps       = [0,     4.4,   10,    15.6,  21.1,  26.7,  32.2,  37.8]
    viscosities = [1.794, 1.546, 1.310, 1.129, 0.982, 0.862, 0.764, 0.682]
    return interp(temp, temps, viscosities)

def MVol(MW, density):
    """Returns an approximation for the molar volume (mL/mol) from the
    molecular weight (g/mol) and density (kg/L)."""

    return (MW / density)

def get_superfont(font):
    """Returns the appropriate superscript fonttype for a given font + size."""

    return font[:-2] + str(int(font[-2:]) - 4)

def get_subfont(font):
    """Returns the appropriate superscript fonttype for a given font + size."""

    return font[:-2] + str(int(font[-2:]) - 2)

def text_converter(formula):
    text = ''
    formula_length = len(formula)

    for i in range(formula_length):

        if   formula[i] == u'\u2080':  text = text + '0'
        elif formula[i] == u'\u2081':  text = text + '1'
        elif formula[i] == u'\u2082':  text = text + '2'
        elif formula[i] == u'\u2083':  text = text + '3'
        elif formula[i] == u'\u2084':  text = text + '4'
        elif formula[i] == u'\u2085':  text = text + '5'
        elif formula[i] == u'\u2086':  text = text + '6'
        elif formula[i] == u'\u2087':  text = text + '7'
        elif formula[i] == u'\u2088':  text = text + '8'
        elif formula[i] == u'\u2089':  text = text + '9'

        elif formula[i] == u'\u2070':  text = text + '^0'
        elif formula[i] == u'\u00B9':  text = text + '^1'
        elif formula[i] == u'\u00B2':  text = text + '^2'
        elif formula[i] == u'\u00B3':  text = text + '^3'
        elif formula[i] == u'\u2074':  text = text + '^4'
        elif formula[i] == u'\u2075':  text = text + '^5'
        elif formula[i] == u'\u2076':  text = text + '^6'
        elif formula[i] == u'\u2077':  text = text + '^7'
        elif formula[i] == u'\u2078':  text = text + '^8'
        elif formula[i] == u'\u2079':  text = text + '^9'
        elif formula[i] == u'\u207A':  text = text + '^+'
        elif formula[i] == u'\u207B':  text = text + '^-'
        else:                          text = text + formula[i]

    return text

def formula_converter(text):
    formula = ''
    text_length = len(text)

    i = 0
    while i < text_length:
        if text[i] == '^':
            if   text[i+1] == '0':  formula = formula + u'\u2070'
            elif text[i+1] == '1':  formula = formula + u'\u00B9'
            elif text[i+1] == '2':  formula = formula + u'\u00B2'
            elif text[i+1] == '3':  formula = formula + u'\u00B3'
            elif text[i+1] == '4':  formula = formula + u'\u2074'
            elif text[i+1] == '5':  formula = formula + u'\u2075'
            elif text[i+1] == '6':  formula = formula + u'\u2076'
            elif text[i+1] == '7':  formula = formula + u'\u2077'
            elif text[i+1] == '8':  formula = formula + u'\u2078'
            elif text[i+1] == '9':  formula = formula + u'\u2079'
            elif text[i+1] == '+':  formula = formula + u'\u207A'
            elif text[i+1] == '-':  formula = formula + u'\u207B'
            i = i + 2
        else:
            if   text[i] == '0':  formula = formula + u'\u2080'
            elif text[i] == '1':  formula = formula + u'\u2081'
            elif text[i] == '2':  formula = formula + u'\u2082'
            elif text[i] == '3':  formula = formula + u'\u2083'
            elif text[i] == '4':  formula = formula + u'\u2084'
            elif text[i] == '5':  formula = formula + u'\u2085'
            elif text[i] == '6':  formula = formula + u'\u2086'
            elif text[i] == '7':  formula = formula + u'\u2087'
            elif text[i] == '8':  formula = formula + u'\u2088'
            elif text[i] == '9':  formula = formula + u'\u2089'
            else:                 formula = formula + text[i]
            i = i + 1

    return formula

def round_to_n(x, n):

    if x == 0: ans = x
    else:      ans = round(x, -int(floor(log10(abs(x))))+ (n - 1))

    return  ans
