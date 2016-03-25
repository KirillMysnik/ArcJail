class _3DTuple(object):
    def __init__(self, *args, **kwargs):
        x, y, z = 0.0, 0.0, 0.0
        if len(args) == 1:
            if hasattr(args[0], '__iter__'):
                x, y, z = map(float, args[0])

            elif isinstance(args[0], _3DTuple):
                x, y, z = args[0].x, args[0].y, args[0].z

            elif isinstance(args[0], _2DTuple):
                x, y = args[0].x, args[0].y

            elif isinstance(args[0], (int, float)):
                x = float(args[0])

            else:
                raise TypeError("Unknown argument type: %s" %
                    type(args[0]))

        elif len(args) == 2:
            if isinstance(args[0], (int, float)):
                x, y = map(float, args)

            elif (isinstance(args[0], _2DTuple) and
                isinstance(args[1], Plane)):

                raise NotImplementedError("Not available in this version")

            else:
                raise TypeError("Unknown argument type: %s" %
                    type(args[0]))

        elif len(args) == 3:
            if isinstance(args[0], (int, float)):
                x, y, z = map(float, args)

            else:
                raise TypeError("Unknown argument type: %s" %
                    type(args[0]))

        elif len(args) > 3:
            raise TypeError("_3DTuple object takes at most 3 arguments "
                "(%s given)" % len(args))

        self.x = float(kwargs.get('x', x))
        self.y = float(kwargs.get('y', y))
        self.z = float(kwargs.get('z', z))

    def __str__(self, *args):
        return "%s %s %s" % (self.x, self.y, self.z)

    def __iter__(self):
        for arg in (self.x, self.y, self.z):
            yield arg


class _2DTuple(object):
    def __init__(self, *args, **kwargs):
        x, y = 0.0, 0.0
        if len(args) == 1:
            if hasattr(args[0], '__iter__'):
                x, y = map(float, args[0])

            elif (isinstance(args[0], _3DTuple) or
                isinstance(args[0], _2DTuple)):

                x, y = args[0].x, args[0].y

            elif isinstance(args[0], (int, float)):
                x = float(args[0])

            else:
                raise TypeError("Unknown argument type: %s" %
                    type(args[0]))

        elif len(args) == 2:
            if isinstance(args[0], (int, float)):
                x, y = map(float, args)

            elif (isinstance(args[0], _3DTuple) and
                isinstance(args[1], Plane)):

                raise NotImplementedError("Not available in this version")

            else:
                raise TypeError("Unknown argument type: %s" %
                    type(args[0]))

        elif len(args) > 2:
            raise TypeError("_2DTuple object takes at most 2 arguments "
                "(%s given)" % len(args))

        self.x = float(kwargs.get('x', x))
        self.y = float(kwargs.get('y', y))

    def __str__(self, *args):
        return "%s %s" % (self.x, self.y)

    def __iter__(self):
        for arg in (self.x, self.y):
            yield arg


class Point(_3DTuple):
    def __add__(self, item):
        if isinstance(item, Vector):
            return Point(self.x+item.x, self.y+item.y, self.z+item.z)

        raise TypeError

    def __sub__(self, item):
        if isinstance(item, Vector):
            return Point(self.x-item.x, self.y-item.y, self.z-item.z)

        raise TypeError

    def __repr__(self):
        return "Point(%s, %s, %s)" % (self.x, self.y, self.z)


class Point2D(_2DTuple):
    def __add__(self, item):
        if isinstance(item, Vector2D):
            return Point2D(self.x+item.x, self.y+item.y)

        raise TypeError

    def __sub__(self, item):
        if isinstance(item, Vector2D):
            return Point2D(self.x-item.x, self.y-item.y)

        raise TypeError

    def __repr__(self):
        return "Point2D(%s, %s)" % (self.x, self.y)


class Vector(_3DTuple):
    def __add__(self, item):
        if isinstance(item, Vector):
            return Vector(self.x+item.x, self.y+item.y, self.z+item.z)

        if isinstance(item, Point):
            return Point(self.x+item.x, self.y+item.y, self.z+item.z)

        raise TypeError

    def __sub__(self, item):
        if isinstance(item, Vector):
            return Vector(self.x-item.x, self.y-item.y, self.z-item.z)

        if isinstance(item, Point):
            return Point(self.x-item.x, self.y-item.y, self.z-item.z)

        raise TypeError

    def __mul__(self, item):
        if isinstance(item, Vector):
            return self.x*item.x + self.y*item.y + self.z*item.z

        if isinstance(item, (int, float)):
            return Vector(self.x*item, self.y*item, self.z*item)

        raise TypeError

    def __truediv__(self, k):
        if isinstance(k, (int, float)):
            return Vector(self.x/k, self.y/k, self.z/k)

        raise TypeError

    def __repr__(self):
        return "Vector(%s, %s, %s)" % (self.x, self.y, self.z)


class Vector2D(_2DTuple):
    def __add__(self, item):
        if isinstance(item, Vector2D):
            return Vector2D(self.x+item.x, self.y+item.y)

        if isinstance(item, Point2D):
            return Point2D(self.x+item.x, self.y+item.y)

        raise TypeError

    def __sub__(self, item):
        if isinstance(item, Vector2D):
            return Vector2D(self.x-item.x, self.y-item.y)

        if isinstance(item, Point2D):
            return Point2D(self.x-item.x, self.y-item.y)

        raise TypeError

    def __mul__(self, item):
        if isinstance(item, Vector2D):
            return self.x*item.x + self.y*item.y

        if isinstance(item, (int, float)):
            return Vector2D(self.x*item, self.y*item)

        raise TypeError

    def __truediv__(self, k):
        if isinstance(k, (int, float)):
            return Vector2D(self.x/k, self.y/k)

        raise TypeError

    def __repr__(self):
        return "Vector2D(%s, %s)" % (self.x, self.y)


class Line2D(object):
    class Line2DEquation(object):	# ax + by + c = 0
        a, b, c = None, None, None
        def __init__(self, points):
            p1, p2 = tuple(points)
            self.a = p2.y - p1.y
            self.b = p1.x - p2.x
            self.c = p1.y*p2.x - p1.x*p2.y

        def __iter__(self):
            for arg in (self.a, self.b, self.c, self.d):
                yield arg

    def __init__(self, *args):
        self.points = set()
        self.equation = None

        if len(args) == 1:
            if hasattr(args[0], '__iter__'):
                for point in args[0]:
                    if isinstance(point, Point2D):
                        self.points |= set((point,))

                    else:
                        raise TypeError("Unknown point type: %s" % point)

            else:
                raise TypeError("Unknown argument type: %s" %
                    type(args[0]))

        elif len(args) == 2:
            if isinstance(args[0], Point2D) and isinstance(args[1], Vector2D):
                p1, p2 = args[0], args[0] + args[1]

            elif isinstance(args[0], Point2D) and isinstance(args[1], Point2D):
                p1, p2 = args[0], args[1]

            else:
                raise TypeError("Unknown argument type: %s" %
                    type(args[0]))

            self.points = set((p1, p2))

        elif len(args) > 2:
            raise TypeError("Line2D object takes at most 2 arguments "
                "(%s given)" % len(args))

        else:
            raise TypeError("Line2D object takes at least 1 argument "
                "(0 given)")

        self.equation = self.Line2DEquation(self.points)

    def __str__(self, *args):
        return "%sx + %sy + %s = 0" % (self.equation.a, self.equation.b,
            self.equation.c)

    def __repr__(self):
        return "Line2D(%s)" % str(self)


class Plane(object):
    class PlaneEquation(object):	# ax + by + cz + d = 0
        a, b, c, d = None, None, None, None

        def __init__(self, points):
            p1, p2, p3 = tuple(points)
            Ax, Ay, Az = p2.x - p1.x, p2.y - p1.y, p2.z - p1.z
            Bx, By, Bz = p3.x - p1.x, p3.y - p1.y, p3.z - p1.z
            self.a = Ay*Bz - Az*By
            self.b = - Ax*Bz + Az*Bx
            self.c = Ax*By - Ay*Bx
            self.d = -self.a*p1.x - self.b*p1.y - self.c*p1.z

        def __iter__(self):
            for arg in (self.a, self.b, self.c, self.d):
                yield arg

    def __init__(self, *args):
        self.points = set()
        self.equation = None

        if len(args) == 1:		# iterable of 3 points
            if hasattr(args[0], '__iter__'):
                for point in args[0]:
                    if isinstance(point, Point):
                        self.points.add(point)

                    else:
                        raise TypeError("Unknown point type: %s" % point)

            else:
                raise TypeError("Unknown argument type: %s" %
                    type(args[0]))

        elif len(args) == 2:	# 1 point, 1 vector OR 2 lines
            if isinstance(args[0], Point):
                point, vec = args

            else:
                vec, point = args

            if not (isinstance(vec, Vector) and isinstance(point, Point)):
                raise TypeError

            # TODO
            raise NotImplementedError("Not available in this version")

        elif len(args) == 3:		# 3 points
            for point in args:
                if isinstance(point, Point):
                    self.points |= set((point,))

                else:
                    raise TypeError("Unknown point type: %s" % point)

        elif len(args) > 3:
            raise TypeError("Plane object takes at most 2 arguments "
                "(%s given)" % len(args))

        else:
            raise TypeError("Plane object takes at least 1 argument "
                "(0 given)")

        self.equation = self.PlaneEquation(self.points)

    def __add__(self, item):
        if isinstance(item, Vector):
            return Plane(*(point+item for point in self.points))

        raise TypeError("Vector expected")

    def __sub__(self, item):
        if isinstance(item, Vector):
            return Plane(*(point-item for point in self.points))

        raise TypeError("Vector expected")

    def __str__(self):
        return "(%s) (%s) (%s)" % tuple(map(str, self.points))

    def __repr__(self):
        return "Plane(%s)" % str(self)


class ConvexArea(object):
    class ConvexAreaFace(Plane):
        # While Plane can be defined by any 3 points,
        # ConvexAreaFace is agreed to be defined by 3 points that belong
        # to this convex area, for example, by 3 vertices.

        # Currently this module doesn't support area definition using
        # random Planes. Please keep this limitation in mind.
        pass

    def __init__(self, *args):
        self.planes = set()
        self._inner_point = Vector()	# We will need a reference point inside
                                        # this area to check if other given
                                        # points belong to the area

        if len(args) == 1:		# iterable of planes
            if hasattr(args[0], '__iter__'):
                for plane in args[0]:
                    if type(plane) is self.ConvexAreaFace:
                        self.planes.add(plane)

                    else:
                        raise TypeError("Unknown plane type: %s" % plane)

            else:
                raise TypeError("Unknown argument type: %s" %
                    type(args[0]))

        else:
            raise TypeError("ConvexArea object takes exactly 1 "
                "argument (%s given)" % len(args))

        if len(self.planes) < 4:
            raise TypeError("ConvexArea must consist of at least 4 planes")

        c = 0
        for plane in self.planes:
            for point in plane.points:
                self._inner_point = self._inner_point + Vector(point)
                c += 1

        self._inner_point = Point(self._inner_point / c)

    def __contains__(self, point):
        if not isinstance(point, Point):
            raise TypeError("Point expected")

        x0, y0, z0 = self._inner_point
        x, y, z = point
        for plane in self.planes:
            a, b, c, d = plane.equation
            ref0 = a*x0 + b*y0 + c*z0 + d
            ref = a*x + b*y + c*z + d
            if (ref != 0) and ((ref > 0) != (ref0 > 0)):
                return False

        return True
