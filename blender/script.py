import os
import math
from random import random
import bpy
from datetime import datetime

from mathutils import Vector

class Box:

    dim_x = 1
    dim_y = 1

    def __init__(self, min_x, min_y, max_x, max_y, dim_x=dim_x, dim_y=dim_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        self.dim_x = dim_x
        self.dim_y = dim_y

    @property
    def x(self):
        return round(self.min_x * self.dim_x)

    @property
    def y(self):
        return round(self.dim_y - self.max_y * self.dim_y)

    @property
    def width(self):
        return round((self.max_x - self.min_x) * self.dim_x)

    @property
    def height(self):
        return round((self.max_y - self.min_y) * self.dim_y)

    def __str__(self):
        return "<Box, x=%i, y=%i, width=%i, height=%i>" % \
               (self.x, self.y, self.width, self.height)

    def to_tuple(self):
        if self.width == 0 or self.height == 0:
            return (0, 0, 0, 0)
        return (self.x, self.y, self.width, self.height)


def camera_view_bounds_2d(scene, cam_ob, me_ob):
    """
    Returns camera space bounding box of mesh object.

    Negative 'z' value means the point is behind the camera.

    Takes shift-x/y, lens angle and sensor size into account
    as well as perspective/ortho projections.

    :arg scene: Scene to use for frame size.
    :type scene: :class:`bpy.types.Scene`
    :arg obj: Camera object.
    :type obj: :class:`bpy.types.Object`
    :arg me: Untransformed Mesh.
    :type me: :class:`bpy.types.Mesh´
    :return: a Box object (call its to_tuple() method to get x, y, width and height)
    :rtype: :class:`Box`
    """

    mat = cam_ob.matrix_world.normalized().inverted()
    me = me_ob.to_mesh(preserve_all_data_layers=True)
    me.transform(me_ob.matrix_world)
    me.transform(mat)

    camera = cam_ob.data
    frame = [-v for v in camera.view_frame(scene=scene)[:3]]
    camera_persp = camera.type != 'ORTHO'

    lx = []
    ly = []

    for v in me.vertices:
        co_local = v.co
        z = -co_local.z

        if camera_persp:
            if z == 0.0:
                lx.append(0.5)
                ly.append(0.5)
            # Does it make any sense to drop these?
            #if z <= 0.0:
            #    continue
            else:
                frame = [(v / (v.z / z)) for v in frame]

        min_x, max_x = frame[1].x, frame[2].x
        min_y, max_y = frame[0].y, frame[1].y

        x = (co_local.x - min_x) / (max_x - min_x)
        y = (co_local.y - min_y) / (max_y - min_y)

        lx.append(x)
        ly.append(y)

    min_x = clamp(min(lx), 0.0, 1.0)
    max_x = clamp(max(lx), 0.0, 1.0)
    min_y = clamp(min(ly), 0.0, 1.0)
    max_y = clamp(max(ly), 0.0, 1.0)

    # bpy.data.meshes.remove(me)

    r = scene.render
    fac = r.resolution_percentage * 0.01
    dim_x = r.resolution_x * fac
    dim_y = r.resolution_y * fac

    return Box(min_x, min_y, max_x, max_y, dim_x, dim_y)


def clamp(x, minimum, maximum):
    return max(minimum, min(x, maximum))


render_dir = "d:/rendering_result"
tex_dir = bpy.path.abspath("//textures")
geometry_file_path = os.path.join(render_dir, "geometry.txt")
target = bpy.data.objects["Suzanne"]
background = bpy.data.objects["Background"]

label = "suzanne"
num_tex = 21
num_results = 100

def getNthImagePath(n):
    return os.path.join(tex_dir, "i-%i.jpg" % n)

for i in range(num_tex):
    bpy.data.images.load(getNthImagePath(i), check_existing=True)
    

with open(geometry_file_path, "w") as file:
    file.write("filename,width,height,class,xmin,ymin,xmax,ymax\n")

    for i in range(num_results):
        ts = int(datetime.timestamp(datetime.now()) * 1000)

        target.rotation_euler[0] = random() * math.pi
        target.rotation_euler[1] = random() * math.pi
        target.rotation_euler[2] = random() * math.pi
        target.location.x = (random() - 0.5) * 3
        target.location.y = (random() - 0.5) * 3
        target.location.z = (random() - 0.5) * 3
        s_mat = target.active_material
        b_mat = background.active_material
        
        color = (random(), random(), random(), 1)
        s_mat.node_tree.nodes['Principled BSDF'].inputs["Base Color"].default_value = color
        
        tex_index = int(random() * num_tex)
        tex = bpy.data.images.get("i-%i.jpg" % tex_index)
        b_mat.node_tree.nodes["Image Texture"].image = tex

        f = "image_" + str(ts) + ".png"
        path = os.path.join(render_dir, f)
        bpy.context.scene.render.filepath = path
        bpy.ops.render.render(write_still = True)
        
        b = camera_view_bounds_2d(bpy.context.scene, bpy.context.scene.camera, target)
        row = "%s,%i,%i,%s,%i,%i,%i,%i" % (f, 512, 512, label, b.x, b.y, b.x + b.width, b.y + b.height)
        file.write(row + "\n")
