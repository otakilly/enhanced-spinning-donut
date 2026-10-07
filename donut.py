import numpy as np
import time
import shutil

resolution = 80
n_points = resolution ** 2 # shapes are sampled at resolution x resolution points

R, r, tau = 2.0, 1.0, 2 * np.pi #main radius,  tube radius, 2pi
MAX_EXTENT = R * np.sqrt(3) # cube corners are the furthest from the centre
CELL_ASPECT = 2.3 # char taller than wide

terminal_width, terminal_height = shutil.get_terminal_size()
screen_width = min(140, terminal_width - 2)
screen_height = min(50, terminal_height - 2)
scale = min((screen_width - 4) / (2 * MAX_EXTENT), (screen_height - 4) * CELL_ASPECT / (2 * MAX_EXTENT), 20.0)

light0 = np.array([1, 1, 1]) / np.sqrt(3) # default light direction

# char palettes : detailed, dense, light, line
palette = [".'`^ \",:;Il!i><~+_-?][}{1)(|\\tfjrxnuvzcXYUJCQL0OZmwqpdbkhaow*#MW&8%B@$", "░▒▓█",".,-~:;=!*#$@",  "| / \\ ( )"]
# colors : cyber, mono, neon
colors = [["\033[38;5;18m", "\033[38;5;27m", "\033[38;5;39m", "\033[38;5;208m", "\033[38;5;220m", "\033[38;5;15m"], ["\033[38;5;232m", "\033[38;5;235m", "\033[38;5;238m", "\033[38;5;241m", "\033[38;5;244m","\033[38;5;247m", "\033[38;5;250m", "\033[38;5;252m", "\033[38;5;254m", "\033[38;5;15m"], ["\033[38;5;39m", "\033[38;5;45m", "\033[38;5;51m", "\033[38;5;165m", "\033[38;5;201m", "\033[38;5;255m"]]

bg, reset = "\033[48;5;232m", "\033[0m"

def rotation(pitch, yaw, roll):# (tangage, lacet, roulis)
    cosT, sinT = np.cos(pitch), np.sin(pitch)
    cosL, sinL = np.cos(yaw), np.sin(yaw)
    cosR, sinR = np.cos(roll), np.sin(roll)
    Rx = np.array([[1, 0, 0], [0, cosR, -sinR], [0, sinR, cosR]])   # roll around x
    Ry = np.array([[cosT, 0, sinT], [0, 1, 0], [-sinT, 0, cosT]])   # pitch around y
    Rz = np.array([[cosL, -sinL, 0], [sinL, cosL, 0], [0, 0, 1]])   # yaw around z
    return Rx @ Ry @ Rz

def light_pos(t): # light moving around with t
    d = np.array([np.cos(t), np.sin(t * 0.5), np.sin(t) - 1.0])
    return d / np.linalg.norm(d)

def projection(position, normal, style, two_sided=False, light=light0):
    # goes through every point, backface culls, then z-buffers into a grid
    grid = [[bg + " " for _ in range(screen_width)] for _ in range(screen_height)]
    z_near = [[-float('inf') for _ in range(screen_width)] for _ in range(screen_height)]

    chars, cols = style

    for i in range(position.shape[1]):
        Px, Py, Pz = position[0, i], position[1, i], position[2, i]
        nx, ny, nz = normal[0, i], normal[1, i], normal[2, i]

        if two_sided: #cant filter points with mobius because it's one face
            if nz < 0:
                nx, ny, nz = -nx, -ny, -nz
        elif nz <= 0:
            continue

        cx = int(screen_width / 2 - 0.5 + scale * Px) #-05 to center
        cy = int(screen_height / 2 - 0.5 - scale * Py / CELL_ASPECT) #CELL_ASPECT keeps the ratio

        # lighting : Lambert's law, I = I0 * cos(alpha).
        I = nx * light[0] + ny * light[1] + nz * light[2]
        if I < 0:
            I = 0
        I = 0.05 + 0.94 * I
        cell = cols[int(I * len(cols))] + chars[int(I * len(chars))] + reset

        # 2x2 stamp to fill the surfaces
        for dy in range(2):
            for dx in range(2):
                x2 = cx + dx
                y2 = cy + dy
                if 0 <= x2 < screen_width and 0 <= y2 < screen_height:
                    if Pz > z_near[y2][x2] - 0.01:
                        z_near[y2][x2] = Pz
                        grid[y2][x2] = cell
    return grid

def show(grid):
    terminal_width, terminal_height = shutil.get_terminal_size()
    left = max(0, (terminal_width - screen_width) // 2)
    top = max(0, (terminal_height - screen_height) // 2)
    image = "\033[2J"   # clear + home
    nb_rows = len(grid)
    for row in range(nb_rows):
        line = grid[row]
        image += f"\033[{top + row + 1};{left + 1}H" + "".join(line) + reset
    print(image, end="", flush=True)

def torus():
    position, normal = np.zeros((3, n_points)), np.zeros((3, n_points))
    theta_range = np.linspace(0, tau, resolution, endpoint=False)   # around the tube
    phi_range = np.linspace(0, tau, resolution, endpoint=False)     # around the ring
    index = 0
    for theta in theta_range:
        cos_t, sin_t = np.cos(theta), np.sin(theta)
        d = R + r * cos_t    # distance from the main axis
        for phi in phi_range:
            cos_p, sin_p = np.cos(phi), np.sin(phi)
            normal[:, index] = [cos_t * cos_p, cos_t * sin_p, sin_t]
            position[:, index] = [d * cos_p, d * sin_p, r * sin_t]
            index += 1
    return position, normal, False

def sphere():
    position, normal = np.zeros((3, n_points)), np.zeros((3, n_points))
    theta_range = np.linspace(0, np.pi, resolution)
    phi_range = np.linspace(0, tau, resolution)
    index = 0
    for theta in theta_range:
        sin_t, cos_t = np.sin(theta), np.cos(theta)
        for phi in phi_range:
            sin_p, cos_p = np.sin(phi), np.cos(phi)
            # spherical -> cartesian
            position[:, index] = [R * sin_t * cos_p, R * sin_t * sin_p, R * cos_t]
            normal[:, index] = [sin_t * cos_p, sin_t * sin_p, cos_t]
            index += 1
    return position, normal, False

def cube():
    position, normal = np.zeros((3, n_points)), np.zeros((3, n_points))
    side = int(np.sqrt(n_points // 6))
    coords = np.linspace(-R, R, side)
    index = 0
    for axis in range(3):            # x, y, z
        for direction in [-1, 1]:    # neg and pos face
            for u in coords:
                for v in coords:
                    if index < n_points:
                        pos = [0, 0, 0]
                        pos[axis] = direction * R
                        pos[(axis + 1) % 3] = u
                        pos[(axis + 2) % 3] = v
                        position[:, index] = pos
                        # normal is a unit vector pointing straight out of the face
                        nvec = [0, 0, 0]
                        nvec[axis] = direction
                        normal[:, index] = nvec
                        index += 1
    return position, normal, False

def mobius():
    position, normal = np.zeros((3, n_points)), np.zeros((3, n_points))
    u_range = np.linspace(0, tau, resolution, endpoint=False)
    v_range = np.linspace(-r / 2, r / 2, resolution)
    index = 0
    for u in u_range:
        cos_u, sin_u = np.cos(u), np.sin(u)
        cos_h, sin_h = np.cos(u / 2), np.sin(u / 2)   # u/2 gives the twist
        for v in v_range:
            position[:, index] = [(R + v * cos_h) * cos_u,
                                  (R + v * cos_h) * sin_u,
                                  v * sin_h]
            # normal = cross product of the two tangents
            tu = np.array([-(R + v * cos_h) * sin_u - 0.5 * v * sin_h * cos_u, (R + v * cos_h) * cos_u - 0.5 * v * sin_h * sin_u, 0.5 * v * cos_h])
            tv = np.array([cos_h * cos_u, cos_h * sin_u, sin_h])
            n = np.cross(tu, tv)
            normal[:, index] = n / (np.linalg.norm(n) + 1e-9)
            index += 1
    return position, normal, True

def interpol(pos_A, norm_A, pos_B, norm_B, style, two_sided):
    # AB = (1-t)A + tB
    steps = 30
    for i in range(steps + 1):
        t = i / steps
        pos, norm = (1 - t) * pos_A + t * pos_B, (1 - t) * norm_A + t * norm_B
        norm = norm / (np.linalg.norm(norm, axis=0) + 1e-9)   # lerp shrinks normals, so renormalise
        show(projection(pos, norm, style, two_sided))
        time.sleep(0.05)

def spin(position, normal, style, two_sided): # shape rotates, light fixed
    pitch, yaw, roll = 0.0, 0.0, 0.0
    for frame in range(100):
        rot = rotation(pitch, yaw, roll)
        show(projection(rot @ position, rot @ normal, style, two_sided))
        pitch += 0.03
        yaw += 0.02
        roll += 0.05
        time.sleep(0.05)

def light_sweep(position, normal, style, two_sided): # shape still, light moving
    tilt, t = rotation(0.4, 0.4, 0.0), 0.0
    position, normal = tilt @ position, tilt @ normal
    for frame in range(100):
        show(projection(position, normal, style, two_sided, light_pos(t)))
        t += 0.2
        time.sleep(0.05)

def play(shapes, style, animation): # run the animation on each shape, interpolate in between
    n = len(shapes)
    for index in range(n):
        pos_A, norm_A, two_A = shapes[index]
        animation(pos_A, norm_A, style, two_A)
        if index + 1 < n:
            pos_B, norm_B, two_B = shapes[index + 1]
            # during a morph, if either shape is two-sided we keep both sides
            interpol(pos_A, norm_A, pos_B, norm_B, style, two_A or two_B)

def main():
    print("\033[?25l", end="", flush=True)   # hide cursor

    shapes = [torus(), cube(), mobius(), sphere()]

    for chars in palette:
        for cols in colors:
            style = (chars, cols)
            play(shapes, style, spin)
            play(shapes, style, light_sweep)

    print("\033[?25h" + reset, end="", flush=True)   # show cursor, reset colours

if __name__ == "__main__":
    main()
