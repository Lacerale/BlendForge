import numpy as np

from app.effects.blend_modes import multiply, screen
from app.layers.base_layer import Layer
from app.renderer.compositor import Compositor


def test_multiply_blend():
    base = np.array([[[0.5, 0.5, 0.5, 1.0]]], dtype=np.float32)
    blend = np.array([[[0.2, 0.4, 0.8, 1.0]]], dtype=np.float32)
    out = multiply(base, blend)
    assert np.allclose(out[0, 0, :3], np.array([0.1, 0.2, 0.4], dtype=np.float32))


def test_screen_blend():
    base = np.array([[[0.25, 0.5, 0.75, 1.0]]], dtype=np.float32)
    blend = np.array([[[0.2, 0.4, 0.6, 1.0]]], dtype=np.float32)
    out = screen(base, blend)
    expected = 1 - ((1 - base) * (1 - blend))
    assert np.allclose(out, expected)


def test_compositor_respects_visibility():
    one = Layer(id="1", name="a", pixels=np.ones((2, 2, 4), dtype=np.float32), visible=False)
    two = Layer(id="2", name="b", pixels=np.zeros((2, 2, 4), dtype=np.float32), visible=True)
    comp = Compositor().composite([one, two])
    assert np.allclose(comp, np.zeros((2, 2, 4), dtype=np.float32))
