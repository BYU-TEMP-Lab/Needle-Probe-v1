import logging
import textwrap

import numpy as np

logger = logging.getLogger(__name__)

def run(x, y):
    times = np.linspace(0, 60, 100)
    temps = np.linspace(20, 100, 100)
    return np.column_stack((times, temps))

def generate_flex_file(file_data, user_selections):
    endtime = file_data["tempData"][0, -1]
    T_amb = file_data["avgT_amb_K"]


    file_contents= f"""
        TITLE 'Needle Probe Radial X-Section (non-lumped properties)'
        COORDINATES YCYLINDER("R","Z")

        VARIABLES
        temp

        DEFINITIONS
        time_end = {endtime:.4f}
        t_step = .001
        T_amb = {T_amb:.4f}
        k
        rho
        cp
        q_gen  = 0

        temp_r2 = EVAL(temp,{user_selections.probe.r_sheath:.4f},0)
        temp_r3 = EVAL(temp,{user_selections.crucible.r_inner:.4f},0)
        # CHECK THIS LINE WITH JAKE
        q_rad = (5.67e-8*((temp)^4 - temp_r3^4)/(1/{e_Ni:.4f} + (1-{e_Crucible:.4f})/{e_Crucible:.4f} * {r_Ni:.4f}/{r_samp:.4f}))

        MATERIALS
        "Crucible" : \tk={k_Crucible:.4f} \trho={rho_Crucible:.4f} \tcp={cp_Crucible:.4f}
        "Sample" : \tk={k_Sample:.4f} \trho={rho_Sample:.4f} \tcp={cp_Sample:.4f}
        "Sheath" : \tk={k_Sheath:.4f} \trho={rho_Sheath:.4f} \tcp={cp_Sheath:.4f}
        "Alumina" : \tk={k_Alumina:.4f} \trho={rho_Alumina:.4f} \tcp={cp_Alumina:.4f}
        "Heating_wires" : \tk={k_Heating_wires:.4f} \trho={rho_Heating_wires:.4f} \tcp={cp_Heating_wires:.4f} \t\tq_gen={qgen_Heating_wires:.4f}
        "Thermocouple" : \tk={k_Thermocouple:.4f} \trho={rho_Thermocouple:.4f} \tcp={cp_Thermocouple:.4f}

        INITIAL VALUES
        temp = T_amb

        EQUATIONS
        temp: \tdiv(k*grad(temp)) + q_gen = (rho*cp)*dt(temp)

        BOUNDARIES

        REGION 1
        USE MATERIAL "Crucible"
        START (0, {h_base:.4f})
        natural(temp) = 0
        LINE to ({r_cruc:.4f}, {h_base:.4f})
        natural(temp) = {h_conv:.4f}*(T_amb - temp)
        LINE to ({r_cruc:.4f}, {h_max:.4f})
        natural(temp) = 0
        LINE to (0, {h_max:.4f})
        LINE to CLOSE

        REGION 2
        USE MATERIAL "Sample"
        START(0, {samp_probe:.4f})
        LINE to ({r_samp:.4f}, {samp_probe:.4f})
        LINE to ({r_samp:.4f}, {h_max:.4f})
        natural(temp) = 0
        LINE to (0, {h_max:.4f})
        LINE to CLOSE

        REGION 3
        USE MATERIAL "Sheath"
        START(0, 0)
        natural(temp) = q_rad
        Contact(temp) = (1/{rTh_sheath_sample:.8f}) * JUMP(temp)
        ARC (center = 0, {Ni_curve:.4f}) to ({r_Ni:.4f}, {Ni_curve:.4f})
        LINE to ({r_Ni:.4f}, {h_max:.4f})
        natural(temp) = 0
        LINE to ({r_Al:.4f}, {h_max:.4f})
        NOBC(temp)
        LINE to ({r_Al:.4f}, {Ni_curve:.4f})
        ARC (center = 0, {Ni_curve:.4f}) to (0, {(r_Ni-r_Al):.4f})
        natural(temp) = 0
        LINE to CLOSE

        REGION 4
        USE MATERIAL "Alumina"
        START(0, {r_Ni - r_Al:.4f})
        Contact(temp) = (1/{rTh_alumina_sheath:.8f}) * JUMP(temp)
        ARC (center = 0, {Ni_curve:.4f}) to ({r_Al:.4f}, {Ni_curve:.4f})
        LINE to ({r_Al:.4f}, {h_max:.4f})
        natural(temp) = 0
        LINE to (0, {h_max:.4f})
        LINE to CLOSE

        REGION 5
        USE MATERIAL "Heating_wires"
        START(0, {r_Ni - r_Al + HW_Ni:.4f})
        natural(temp) = 0
        LINE to (0, {r_Ni - r_Al + HW_Ni + r_wires * 2:.4f})
        NOBC(temp)
        ARC (center = 0, {r_Ni - r_Al + HW_Ni + HW_curve:.4f}) to ({r_wir_i:.4f}, {r_Ni - r_Al + HW_Ni + HW_curve:.4f})
        LINE to ({r_wir_i:.4f}, {h_max:.4f})
        natural(temp) = 0
        LINE to ({r_wir_o:.4f}, {h_max:.4f})
        NOBC(temp)
        LINE to ({r_wir_o:.4f}, {r_Ni - r_Al + HW_Ni + HW_curve:.4f})
        ARC (center = 0, {r_Ni - r_Al + HW_Ni + HW_curve:.4f}) to CLOSE

        REGION 6
        USE MATERIAL "Thermocouple"
        START(0, {h_max:.4f})
        natural(temp) = 0
        LINE to ({r_tc:.4f}, {h_max:.4f})
        LINE to ({r_tc:.4f}, {TC_loc:.4f})
        ARC (center = 0, {TC_loc:.4f}) to (0, {TC_loc - 0.001:.4f})
        natural(temp) = 0
        LINE to CLOSE

        TIME
        0 BY t_step TO time_end

        HISTORIES
        History(Temp) AT (0.0, 0.05) export format "#t#r,#i" file="temp.txt"

        END
    """

    file_contents = textwrap.dedent(file_contents).strip()
    logger.info(textwrap.dedent(file_contents).strip())


def run_flexpde2(par_vector, par_names, SolvNam, endtime, flexpde_path=r'C:\Program Files\FlexPDE7\FlexPDE7.exe'):
    """
    Generates a full FlexPDE file from parameters, runs FlexPDE, and returns the temp vs time array.
    """
    # --- Geometry & fixed constants ---
    r_tc = 0.094313e-3
    TC_loc = 0.05
    r_wires = 0.094313e-3
    r_wir_o = 0.485942e-3
    r_wir_i = 0.297315e-3
    r_wir_mid = 0.391629E-3
    HW_curve = 4.85942e-4
    HW_Ni = 0.002
    r_Al = 0.8293e-3
    r_Ni = 1.388E-3
    Ni_curve = 0.001
    samp_probe = -0.001
    r_cruc = 0.0127
    h_max = 0.1
    h_base = -0.01 + samp_probe
    vol_wires = np.pi*r_wires**2*(h_max*2) + (np.pi**2 * r_wires**2 * r_wir_mid)
    L = h_max - (r_Ni - r_Al + HW_Ni + HW_curve) + 2*np.pi*r_wir_mid

    # --- Assign parameters ---
    k_Thermocouple = par_vector[0]
    rho_Thermocouple = par_vector[1]
    cp_Thermocouple = par_vector[2]

    k_wire = par_vector[3]
    rho_wire = par_vector[4]
    cp_wire = par_vector[5]

    k_Alumina = par_vector[6]*np.exp((-1.5*(par_vector[20]/100))/(1-(par_vector[20]/100)))
    rho_Alumina = par_vector[7]
    cp_Alumina = par_vector[8]

    k_Sheath = par_vector[9]
    rho_Sheath = par_vector[10]
    cp_Sheath = par_vector[11]
    e_Ni = par_vector[12]

    k_Crucible = par_vector[13]
    rho_Crucible = par_vector[14]
    cp_Crucible = par_vector[15]
    e_Crucible = par_vector[16]

    k_Sample = par_vector[23]
    if 'Sample' in SolvNam:
        rho_cp_Sample = par_vector[26]
        rho_Sample = 1
        cp_Sample = rho_cp_Sample / rho_Sample
    else:
        rho_Sample = par_vector[24]
        cp_Sample = par_vector[25]

    scatter = par_vector[17]
    h_conv = par_vector[18]
    q_gen_wire = par_vector[19]/vol_wires
    rTh_alumina_sheath = par_vector[21]
    rTh_sheath_sample = par_vector[22]
    T_amb = par_vector[27]
    r_samp = par_vector[28]

    # Lumped wire properties
    k_Heating_wires = ((2.0595e-10 + L*4.0826e-8)*k_Alumina + (3.4381e-11 + L*5.5889e-9)*k_wire) / (4.119e-10 + L*8.1652e-8)
    rho_Heating_wires = ((2.0595e-10 + L*4.0826e-8)*rho_Alumina + (3.4381e-11 + L*5.5889e-9)*rho_wire) / (4.119e-10 + L*8.1652e-8)
    cp_Heating_wires = ((2.0595e-10 + L*4.0826e-8)*cp_Alumina + (3.4381e-11 + L*5.5889e-9)*cp_wire) / (4.119e-10 + L*8.1652e-8)
    qgen_Heating_wires = ((3.4381e-11 + L*5.5889e-9)*q_gen_wire) / (4.119e-10 + L*8.1652e-8)

    # --- Generate PDE filename ---
    uniqueID = str(np.random.randint(1000, 9999))
    filename = f"Flex_{uniqueID}.pde"

    # --- PDE content ---
    pde_lines = [
        "TITLE 'Needle Probe Radial X-Section (non-lumped properties)'",
        "COORDINATES YCYLINDER('R','Z')",
        "VARIABLES",
        "temp",
        "DEFINITIONS",
        f"time_end = {endtime:.4f}",
        "t_step = 0.001",
        f"T_amb = {T_amb:.4f}",
        "k", "rho", "cp",
        f"q_gen = 0",
        f"temp_r2 = EVAL(temp,{r_Ni:.6f},0)",
        f"temp_r3 = EVAL(temp,{r_samp:.6f},0)",
        f"q_rad = (5.67e-8*((temp)^4 - temp_r3^4)/(1/{e_Ni:.4f} + (1-{e_Crucible:.4f})/{e_Crucible:.4f} * {r_Ni:.4f}/{r_samp:.4f}))",
        "MATERIALS",
        f'"Crucible" : k={k_Crucible:.4f} rho={rho_Crucible:.4f} cp={cp_Crucible:.4f}',
        f'"Sample" : k={k_Sample:.4f} rho={rho_Sample:.4f} cp={cp_Sample:.4f}',
        f'"Sheath" : k={k_Sheath:.4f} rho={rho_Sheath:.4f} cp={cp_Sheath:.4f}',
        f'"Alumina" : k={k_Alumina:.4f} rho={rho_Alumina:.4f} cp={cp_Alumina:.4f}',
        f'"Heating_wires" : k={k_Heating_wires:.4f} rho={rho_Heating_wires:.4f} cp={cp_Heating_wires:.4f} q_gen={qgen_Heating_wires:.4f}',
        f'"Thermocouple" : k={k_Thermocouple:.4f} rho={rho_Thermocouple:.4f} cp={cp_Thermocouple:.4f}',
        "INITIAL VALUES",
        "temp = T_amb",
        "EQUATIONS",
        "temp: div(k*grad(temp)) + q_gen = (rho*cp)*dt(temp)",
        "TIME",
        "0 BY t_step TO time_end",
        "HISTORIES",
        'History(Temp) AT (0.0, 0.05) export format "#t#r,#i" file="temp.txt"',
        "END"
    ]

    # Write PDE file
    with open(filename, 'w') as f:
        f.write("\n".join(pde_lines))

    # --- Run FlexPDE ---
    command = f'"{flexpde_path}" "{filename}" /r -S'
    subprocess.run(command, shell=True)

    # Wait for temp.txt output
    while not os.path.exists("temp.txt"):
        time.sleep(0.1)

    # Read the FlexPDE output
    temp_tvt = np.loadtxt("temp.txt", delimiter=',', skiprows=8)

    return uniqueID, filename, temp_tvt