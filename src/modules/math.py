import math


class Vector:

    @staticmethod
    def cross_product(u, v):
        return (u[1]*v[2] - u[2]*v[1],
                u[2]*v[0] - u[0]*v[2],
                u[0]*v[1] - u[1]*v[0])

    @staticmethod
    def dot_product(u, v):
        return u[0]*v[0] + u[1]*v[1] + u[2]*v[2]

    @staticmethod
    def magnitude(v):
        return math.sqrt(Vector.dot_product(v, v))

    @staticmethod
    def angle_between_vectors(u, v):
        """ Compute the angle between vector u and v """
        dp = Vector.dot_product(u, v)
        if dp == 0:
            return 0
        um = Vector.magnitude(u)
        vm = Vector.magnitude(v)
        return math.acos(dp / (um*vm)) * (180. / math.pi)

    def euler_to_vector(pitch, heading):

        xzLen = math.cos(pitch)
        x = xzLen * math.cos(heading)
        y = math.sin(pitch)
        z = xzLen * math.sin(-heading)


        return (x, y, z)