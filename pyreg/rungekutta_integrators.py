"""
Simple (explicit) Runge-Kutta integrators to forward integrate dynamic forward models
"""
from abc import ABCMeta, abstractmethod

import torch
from torch.autograd import Variable

import numpy as np

class RKIntegrator(object):

    __metaclass__ = ABCMeta

    def __init__(self,f,u,pars,params):

        self.nrOfTimeSteps = params[('number_of_time_steps', 10,
                                                'Number of time-steps to integrate the PDE')]
        self.f = f

        if pars is None:
            self.pars = []
        else:
            self.pars = pars

        if u is None:
            self.u = lambda t,pars: []
        else:
            self.u = u

    def set_number_of_time_steps(self, nr):
        self.nrOfTimeSteps = nr

    def get_number_of_time_steps(self):
        return self.nrOfTimeSteps

    def solve(self,x,fromT,toT):
        # arguments need to be list so we can pass multiple variables at the same time
        assert type(x)==list
        timepoints = np.linspace(fromT, toT, self.nrOfTimeSteps + 1)
        dt = timepoints[1]-timepoints[0]
        currentT = fromT
        #iter = 0
        for i in range(0, self.nrOfTimeSteps):
            #print('RKIter = ' + str( iter ) )
            #iter+=1
            x = self.solve_one_step(x, currentT, dt)
            currentT += dt
        #print( x )
        return x

    def xpyts(self,x,y,v):
        # x plus y times scalar
        return [a+b*v for a,b in zip(x,y)]

    def xts(self,x,v):
        # x times scalar
        return [a*v for a in x]

    def xpy(self,x,y):
        return [a+b for a,b in zip(x,y)]

    @abstractmethod
    def solve_one_step(self, x, t, dt):
        # x and output of f are expected to be lists
        pass

class EulerForward(RKIntegrator):

    def solve_one_step(self, x, t, dt):
        #xp1 = [a+b*dt for a,b in zip(x,self.f(t,x,self.u(t)))]
        xp1 = self.xpyts(x,self.f(t,x,self.u(t, self.pars), self.pars),dt)
        return xp1

class RK4(RKIntegrator):

    def solve_one_step(self, x, t, dt):
        k1 = self.xts( self.f(t,x,self.u(t,self.pars), self.pars), dt )
        k2 = self.xts( self.f(t+0.5*dt, self.xpyts(x, k1, 0.5), self.u(t+  0.5 * dt, self.pars), self.pars), dt )
        k3 = self.xts( self.f(t+0.5*dt, self.xpyts(x, k2, 0.5), self.u(t + 0.5 * dt, self.pars), self.pars), dt)
        k4 = self.xts( self.f(t+dt, self.xpy(x, k3), self.u(t + dt, self.pars), self.pars), dt)

        # now iterate over all the elements of the list describing state x
        xp1 = []
        for i in range(len(x)):
            xp1.append( x[i] + k1[i]/6. + k2[i]/3. + k3[i]/3. + k4[i]/6. )

        return xp1

