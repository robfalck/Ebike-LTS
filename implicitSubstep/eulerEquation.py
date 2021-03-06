import numpy as np
import openmdao.api as om

class eulerEquation(om.ImplicitComponent):
    def initialize(self):
        self.options.declare('num_nodes', types=int)

    def setup(self):
        nn = self.options['num_nodes']

        #constants
        self.add_input('M', val=300.0, desc='total mass', units='kg')
        self.add_input('g', val=9.81, desc='gravity', units='m/s**2')
        self.add_input('rho', val=1.2, desc='air density', units='kg/m**3')
        self.add_input('Cl', val=0.03, desc='lift coefficient', units=None)
        self.add_input('Cd', val=0.41, desc='drag coefficient', units=None)
        self.add_input('rt', val=0.1, desc='wheel toroid radius', units=None)
        self.add_input('r', val=0.3, desc='wheel radius', units='m')
        self.add_input('h', val=0.6, desc='CoG height', units=None)
        self.add_input('Ixx', val=19, desc='roll moment of inertia', units='kg*m**2')
        self.add_input('Iyy', val=5, desc='pitch moment of inertia', units='kg*m**2') # guesses
        self.add_input('Izz', val=5, desc='yaw moment of inertia', units='kg*m**2') #
        self.add_input('Igy', val=2.1, desc='gyroscopic moment of inertia', units='kg*m**2')

        #states
        self.add_input('Phi', val=np.zeros(nn), desc='roll', units='rad')
        self.add_input('Phidot', val=np.zeros(nn), desc='roll rate', units='rad/s')
        self.add_input('Phiddot', val=np.zeros(nn), desc='roll rate2', units='rad/s**2')
        self.add_input('Beta', val=np.zeros(nn), desc='drift angle', units='rad')
        self.add_input('alpha', val=np.zeros(nn), desc='relative heading', units='rad')
        self.add_input('alphadot', val=np.zeros(nn), desc='relative heading rate', units='rad/s')
        self.add_input('nu', val=np.zeros(nn), desc='road curvature x-z', units='1/m')
        self.add_input('k', val=np.zeros(nn), desc='road curvature x-y', units='1/m')
        self.add_input('tau', val=np.zeros(nn), desc='road curvature torsional', units='1/m')
        self.add_input('sig', val=np.zeros(nn), desc='road slope', units='rad')
        self.add_input('V', val=np.zeros(nn), desc='forward velocity', units='m/s')
        self.add_input('Vdot', val=np.zeros(nn), desc='forward acceleration', units='m/s**2')
        self.add_input('n', val=np.zeros(nn), desc='road lateral position', units='m')
        self.add_input('z', val=np.zeros(nn), desc='vertical displacement', units='m')
        self.add_input('zdot', val=np.zeros(nn), desc='vertical velocity', units='m/s')
        self.add_input('zddot', val=np.zeros(nn), desc='vertical acceleration', units='m/s**2')
        self.add_input('sdot', val=np.zeros(nn), desc='road longitudinal velocity', units='m/s')
        self.add_input('Omega_z', val=np.zeros(nn), desc='yaw rate', units='rad/s')
        self.add_input('omega_w', val=np.zeros(nn), desc='wheel spin', units='rad/s')

        #outputs
        self.add_output('Betadot', val=np.zeros(nn), desc='drift rate', units='rad/s', lower = -5, upper = 5)

        self.declare_coloring(wrt='*', method='cs', tol=1.0E-12, show_sparsity=True)

    def apply_nonlinear(self, inputs, outputs, residuals):
        M = inputs['M']
        g = inputs['g']
        rho = inputs['rho']
        Cl = inputs['Cl']
        Cd = inputs['Cd']
        rt = inputs['rt']
        r = inputs['r']
        h = inputs['h']
        Ixx = inputs['Ixx']
        Iyy = inputs['Iyy']
        Izz = inputs['Izz']
        Igy = inputs['Igy']

        Phi = inputs['Phi']
        Phidot = inputs['Phidot']
        Phiddot = inputs['Phiddot']
        Beta = inputs['Beta']
        alpha = inputs['alpha']
        alphadot = inputs['alphadot']
        nu = inputs['nu']
        tau = inputs['tau']
        sig = inputs['sig']
        V = inputs['V']
        Vdot = inputs['Vdot']
        n = inputs['n']
        k = inputs['k']
        z = inputs['z']
        zdot = inputs['zdot']
        zddot= inputs['zddot']
        sdot = inputs['sdot']
        Omega_z = inputs['Omega_z']
        omega_w = inputs['omega_w']

        Betadot = outputs['Betadot']


        Omega_x = sdot*(nu*np.sin(alpha)+tau*np.cos(alpha))
        Omega_y = sdot*(nu*np.cos(alpha)-tau*np.sin(alpha))

        sddot = - (V*(np.sin(alpha)*Betadot - np.sin(alpha)*alphadot + np.cos(alpha)*Beta*alphadot))/(k*n - 1) - Vdot*(np.cos(alpha) + np.sin(alpha)*Beta)/(k*n - 1)
        Omegadot_x = - ((tau*np.cos(alpha) + nu*np.sin(alpha))*Vdot*(np.cos(alpha) + np.sin(alpha)*Beta))/(k*n - 1) - (V*(tau*np.cos(alpha) + nu*np.sin(alpha))*(np.sin(alpha)*Betadot - np.sin(alpha)*alphadot + np.cos(alpha)*Beta*alphadot))/(k*n - 1) - (V*(nu*np.cos(alpha)*alphadot - tau*np.sin(alpha)*alphadot)*(np.cos(alpha) + np.sin(alpha)*Beta))/(k*n - 1)

        V_x = V
        V_y = -V*Beta
        V_z = sdot*tau*n

        Vdot_y = -Vdot*Beta-V*Betadot
        Vdot_z = sddot*tau*n

        L=0.5*rho*Cl*V**2

        T0 = (h-rt)*(np.sin(Phi)*(zddot-Omega_y*V_x+Omega_y*V_x+Omega_x*V_y+Vdot_z -g) - np.cos(Phi)*(Vdot_y-2*Omega_x*zdot+Omega_x+V_z+g*sig*np.sin(alpha))) \
            + (h-rt)*(rt-z)*(2*np.cos(Phi)*Omegadot_x-2*np.cos(Phi)*Omega_z*Omega_y+np.sin(Phi)*(Omega_y**2+Omega_z**2-Phidot**2-2*Omega_x*Phidot)) \
            + (h-rt)**2*(Omegadot_x + np.sin(Phi)*np.cos(Phi)*(Omega_y**2-Omega_z**2)-2*np.cos(Phi)**2*Omega_x*Omega_y) \
            + (z**2 -r*rt*z)*Omegadot_x + (h-z)*(h-2*rt+z)*Omega_y*Omega_z + (rt-z)*(Vdot_y-V_z*Omega_x+V_x*Omega_z-2*zdot*Omega_x - g*sig*np.sin(alpha))

        residuals['Betadot'] = ((-(h-rt)*(z-rt)*np.cos(Phi)+(h-rt)**2)*M+Ixx)*Phiddot + Ixx*Omegadot_x + (Omega_z*np.cos(Phi)-Omega_y*np.sin(Phi))*Igy*omega_w \
                            + np.sin(Phi)*(z-rt)*L + (Iyy-Izz)*(np.cos(Phi)*np.sin(Phi)*(Omega_y**2-Omega_z**2)+Omega_y*Omega_z*(1-2*np.cos(Phi)**2)) +M*T0
