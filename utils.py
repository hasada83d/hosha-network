# utils.py
import math
import numpy as np

class RD:
    """
    RD クラスは、基準点からの相対座標計算をサポートします。
    """
    @classmethod
    def set_origin(cls, x, y):
        cls.x = x
        cls.y = y

    @classmethod
    def getRD(cls, X, Y):
        _x = X - cls.x
        _y = Y - cls.y
        r = math.sqrt(_x**2 + _y**2)
        rad = math.atan2(_y, _x)
        degree = math.degrees(rad)
        return r, degree

    @classmethod
    def getXY(cls, r, degree):
        rad = math.radians(degree)
        x = r * math.cos(rad)
        y = r * math.sin(rad)
        return x + cls.x, y + cls.y

def average_angle(angle1, angle2):
    """
    角度 angle1, angle2（ラジアン）の平均（二等分角）を求める関数。
    角度差が π を超えた場合も正しく補正します。
    """
    diff = angle2 - angle1
    diff = np.arctan2(np.sin(diff), np.cos(diff))
    bisector = angle1 + diff / 2.0
    return np.arctan2(np.sin(bisector), np.cos(bisector))
