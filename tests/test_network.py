import unittest

import numpy as np

import data

import dotdot  # pylint: disable=unused-import
import leabra



class NetworkTestAPI(unittest.TestCase):

    def test_simple_usage(self):
        """Test the basic Network API"""
        input_layer  = leabra.Layer(4, name='input_layer')
        output_spec  = leabra.LayerSpec(g_i=1.5, ff=1, fb=0.5, fb_dt=1/1.4, ff0=0.1)
        output_layer = leabra.Layer(2, spec=output_spec, name='output_layer')

        conspec = leabra.ConnectionSpec(proj="full", lrule='leabra')
        conn    = leabra.Connection(input_layer, output_layer, spec=conspec)

        network = leabra.Network(layers=[input_layer, output_layer], connections=[conn])

        network.set_inputs({'input_layer': [1.0, 1.0, 0.0, 0.0]})
        network.set_outputs({'output_layer': [1.0, 0.0]})

        for _ in range(20):
            network.trial()

        self.assertTrue(True)


class NetworkTestBehavior(unittest.TestCase):
    """Check that the Network behaves as it should.

    The checks are concerned with consistency with the equations that define the
    network's and overall learning behavior. These test should pass on the
    emergent implementation as well.
    """

    def test_simple_pattern_learning(self):
        """Quantitative test on the pair of neurons scenario"""
        check = True

        for inhib in [True, False]:
            if inhib:
                emergent_data = data.parse_weights('neuron_pair_inhib.dat')
                cycle_data    = data.parse_unit('neuron_pair_inhib_cycle.dat')
            else:
                emergent_data = data.parse_weights('neuron_pair.dat')
                cycle_data    = data.parse_unit('neuron_pair_cycle.dat')

            u_spec = leabra.UnitSpec(act_thr=0.5, act_gain=100, act_sd=0.005,
                                     g_bar_e=1.0, g_bar_i=1.0, g_bar_l=0.1,
                                     e_rev_e=1.0, e_rev_i=0.25, e_rev_l=0.3,
                                     avg_l_min=0.2, avg_l_init=0.4, avg_l_gain=2.5,
                                     adapt_on=False)
            input_layer  = leabra.Layer(1, unit_spec=u_spec, name='input_layer')
            g_i = 1.5 if inhib else 0.0
            output_spec  = leabra.LayerSpec(g_i=g_i, ff=0.0, fb=0.5, fb_dt=1/1.4, ff0=0.1)
            output_layer = leabra.Layer(1, spec=output_spec, unit_spec=u_spec, name='output_layer')
            for u in output_layer.units:
                u.avg_l_lrn = 1.0
            conspec = leabra.ConnectionSpec(proj='full', lrule='leabra', lrate=0.04,
                                            m_lrn=0.0, rnd_mean=0.5, rnd_var=0.0)
            conn    = leabra.Connection(input_layer, output_layer, spec=conspec)

            network = leabra.Network(layers=[input_layer, output_layer], connections=[conn])
            network.set_inputs({'input_layer': [0.95]})
            network.set_outputs({'output_layer': [0.95]})

            logs = {'wt': [], 'sse': [], 'output_act_m': []}
            for t in range(50):
                logs['wt'].append(conn.links[0].wt)
                sse = network.trial()
                logs['sse'].append(sse)
                logs['output_act_m'].append(output_layer.units[0].act_m)

            output_unit = output_layer.units[0]
            for name in output_unit.logs.keys():
                for t, (py, em) in enumerate(list(zip(output_unit.logs[name], cycle_data[name]))[:50]):
                    if not np.allclose(py, em, rtol=0, atol=1e-05):
                        print('{}:{:2d} [py] {:.10f} != {:.10f} [emergent] ({}inhib) diff={:g}'.format(
                               name, t,   py,        em,       '' if inhib else 'no ', py-em))
                        check = False

        self.assertTrue(check)


    def test_netin_scaling(self):
        """Quantitative test on the netin scaling scenario"""
        check = True
        cycle_data = data.parse_unit('netin.dat')

        def build_network():
            u_spec = leabra.UnitSpec(act_thr=0.5, act_gain=100, act_sd=0.005,
                                     g_bar_e=1.0, g_bar_l=0.1, g_bar_i=1.0,
                                     e_rev_e=1.0, e_rev_l=0.3, e_rev_i=0.25,
                                     avg_l_min=0.2, avg_l_init=0.4, avg_l_gain=2.5,
                                     adapt_on=False)
            # layers
            input0_layer  = leabra.Layer(4, unit_spec=u_spec, name='input0_layer')
            input1_layer  = leabra.Layer(4, unit_spec=u_spec, name='input1_layer')
            output_spec  = leabra.LayerSpec(lay_inhib=False)
            output_layer = leabra.Layer(4, spec=output_spec, unit_spec=u_spec, name='output_layer')
            # connections
            conn_spec0 = leabra.ConnectionSpec(proj='1to1', lrule=None, rnd_mean=0.5, rnd_var=0.0,
                                               wt_scale_abs=1.0, wt_scale_rel=1.0)
            conn_spec1 = leabra.ConnectionSpec(proj='1to1', lrule=None, rnd_mean=0.5, rnd_var=0.0,
                                               wt_scale_abs=2.0, wt_scale_rel=1.0)
            conn0 = leabra.Connection(input0_layer, output_layer, spec=conn_spec0)
            conn1 = leabra.Connection(input1_layer, output_layer, spec=conn_spec1)
            # network
            network = leabra.Network(layers=[input0_layer, input1_layer, output_layer],
                                     connections=[conn0, conn1])
            network.set_inputs({'input0_layer': [0.5, 0.95, 0.0, 0.25],
                                'input1_layer': [0.0, 0.5, 0.95, 0.75]})
            return network

        def compute_logs(network):
            logs = {'net': [], 'act': []}
            output_layer = network.layers[2]
            for t in range(200):
                network.cycle()
                logs['net'].append(np.array([u.net for u in output_layer.units]))
                logs['act'].append(np.array([u.act for u in output_layer.units]))
            return logs

        network = build_network()
        logs = compute_logs(network)

        for name in logs.keys():
            for t, (py, em) in enumerate(list(zip(logs[name], cycle_data[name]))[:200]):
                if not np.allclose(py, em, rtol=0, atol=1e-05):
                    print('{}:{:2d} [py] {} != {} [emergent] diff={}'.format(
                           name, t,   py,        em, py-em))
                    check = False

        self.assertTrue(check)


    def test_std_project(self):
        """Quantitative test on the template Leabra project"""
        check = True
        cycle_data = data.parse_unit('LeabraStd.dat')

        def build_network():
            u_spec = leabra.UnitSpec(act_thr=0.5, act_gain=100, act_sd=0.005,
                                     g_bar_e=1.0, g_bar_l=0.1, g_bar_i=1.0,
                                     e_rev_e=1.0, e_rev_l=0.3, e_rev_i=0.25,
                                     avg_l_min=0.2, avg_l_init=0.4, avg_l_gain=2.5,
                                     adapt_on=False)
            # layers
            input0_layer  = leabra.Layer(4, unit_spec=u_spec, name='input0_layer')
            input1_layer  = leabra.Layer(4, unit_spec=u_spec, name='input1_layer')
            output_spec  = leabra.LayerSpec(lay_inhib=False)
            output_layer = leabra.Layer(4, spec=output_spec, unit_spec=u_spec, name='output_layer')
            # connections
            conn_spec0 = leabra.ConnectionSpec(proj='1to1', lrule=None, rnd_mean=0.5, rnd_var=0.0,
                                               wt_scale_abs=1.0, wt_scale_rel=1.0)
            conn_spec1 = leabra.ConnectionSpec(proj='1to1', lrule=None, rnd_mean=0.5, rnd_var=0.0,
                                               wt_scale_abs=2.0, wt_scale_rel=1.0)
            conn0 = leabra.Connection(input0_layer, output_layer, spec=conn_spec0)
            conn1 = leabra.Connection(input1_layer, output_layer, spec=conn_spec1)
            # network
            network = leabra.Network(layers=[input0_layer, input1_layer, output_layer],
                                     connections=[conn0, conn1])
            network.set_inputs({'input0_layer': [0.5, 0.95, 0.0, 0.25],
                                'input1_layer': [0.0, 0.5, 0.95, 0.75]})
            return network

        def compute_logs(network):
            logs = {'net': [], 'act': []}
            output_layer = network.layers[2]
            for t in range(200):
                network.cycle()
                logs['net'].append(np.array([u.net for u in output_layer.units]))
                logs['act'].append(np.array([u.act for u in output_layer.units]))
            return logs

        network = build_network()
        logs = compute_logs(network)

        for name in logs.keys():
            for t, (py, em) in enumerate(list(zip(logs[name], cycle_data[name]))[:200]):
                if not np.allclose(py, em, rtol=0, atol=1e-05):
                    print('{}:{:2d} [py] {} != {} [emergent] diff={}'.format(
                           name, t,   py,        em, py-em))
                    check = False

        self.assertTrue(check)


if __name__ == '__main__':
    unittest.main()
