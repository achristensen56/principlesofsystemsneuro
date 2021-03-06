import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib import animation
from itertools import combinations
import seaborn as sns
from utils import *

class Particle:
    """A class representing a two-dimensional particle."""

    def __init__(self, x, y, vx, vy, radius=0.01, styles=None):
        """Initialize the particle's position, velocity, and radius.

        Any key-value pairs passed in the styles dictionary will be passed
        as arguments to Matplotlib's Circle patch constructor.

        """

        self.r = np.array((x, y)).astype('float32')
        self.v = np.array((vx, vy)).astype('float32')
        self.radius = radius
        self.mass = self.radius**2
        self.delete = False
        self.styles = styles
        if not self.styles:
            # Default circle styles
            self.styles = {'edgecolor': 'c', 'fill': False}

    # For convenience, map the components of the particle's position and
    # velocity vector onto the attributes x, y, vx and vy.
    @property
    def x(self):
        return self.r[0]
    @x.setter
    def x(self, value):
        self.r[0] = value
    @property
    def y(self):
        return self.r[1]
    @y.setter
    def y(self, value):
        self.r[1] = value
    @property
    def vx(self):
        return self.v[0]
    @vx.setter
    def vx(self, value):
        self.v[0] = value
    @property
    def vy(self):
        return self.v[1]
    @vy.setter
    def vy(self, value):
        self.v[1] = value

    def overlaps(self, other):
        """Does the circle of this Particle overlap that of other?"""

        return np.hypot(*(self.r - other.r)) < self.radius + other.radius

    def draw(self, ax):
        """Add this Particle's Circle patch to the Matplotlib Axes ax."""

        circle = Circle(xy=self.r, radius=self.radius, **self.styles)
        ax.add_patch(circle)
        return circle

    def advance(self, dt):
        """Advance the Particle's position forward in time by dt."""
        
        self.r += self.v * dt
        #add damping according to mass
        self.v -= .5*self.mass*dt
        
        
class Simulation:
    """A class for a simple hard-circle molecular dynamics simulation.

    The simulation is carried out on a square domain: 0 <= x < 1, 0 <= y < 1.

    """

    ParticleClass = Particle

    def __init__(self, n, radius=0.01, styles=None, srf = generate_tempgrad(.05)):
        """Initialize the simulation with n Particles with radii radius.

        radius can be a single value or a sequence with n values.

        Any key-value pairs passed in the styles dictionary will be passed
        as arguments to Matplotlib's Circle patch constructor when drawing
        the Particles.

        """

        self.init_particles(n, radius, styles)
        self.dt = 0.01
        self.srf = srf

    def place_particle(self, rad, styles):
        # Choose x, y so that the Particle is entirely inside the
        # domain of the simulation.
        x, y = rad + (1 - 2*rad) * np.random.random(2)
        # Choose a random velocity (within some reasonable range of
        # values) for the Particle.
        vr = 0.05 * np.sqrt(np.random.random()) + 0.05
        vphi = 0*np.pi * np.random.random()
        vx, vy = vr * np.cos(vphi), vr * np.sin(vphi)
        particle = self.ParticleClass(x, y, vx, vy, rad, styles)
        # Check that the Particle doesn't overlap one that's already
        # been placed.
        for p2 in self.particles:
            if p2.overlaps(particle):
                break
        else:
            self.particles.append(particle)
            return True
        return False

    def init_particles(self, n, radius, styles=None):
        """Initialize the n Particles of the simulation.

        Positions and velocities are chosen randomly; radius can be a single
        value or a sequence with n values.

        """

        try:
            iterator = iter(radius)
            assert n == len(radius)
        except TypeError:
            # r isn't iterable: turn it into a generator that returns the
            # same value n times.
            def r_gen(n, radius):
                for i in range(n):
                    yield radius
            radius = r_gen(n, radius)

        self.n = n
        self.particles = []
        for i, rad in enumerate(radius):
            # Try to find a random initial position for this particle.
            while not self.place_particle(rad, styles):
                pass

    def change_velocities(self, p1, p2):
        """
        Particles p1 and p2 have collided elastically: update their
        velocities.

        """
        
        m1, m2 = p1.mass, p2.mass
        M = m1 + m2
        r1, r2 = p1.r, p2.r
        d = np.linalg.norm(r1 - r2)**2
        v1, v2 = p1.v, p2.v
        u1 = v1 - 2*m2 / M * np.dot(v1-v2, r1-r2) / d * (r1 - r2)
        u2 = v2 - 2*m1 / M * np.dot(v2-v1, r2-r1) / d * (r2 - r1)
        p1.v = u1
        p2.v = u2

    def handle_collisions(self):
        """Detect and handle any collisions between the Particles.

        When two Particles collide, they do so elastically: their velocities
        change such that both energy and momentum are conserved.

        """ 

        # We're going to need a sequence of all of the pairs of particles when
        # we are detecting collisions. combinations generates pairs of indexes
        # into the self.particles list of Particles on the fly.
        pairs = combinations(range(self.n), 2)
        for i,j in pairs:
            if self.particles[i].overlaps(self.particles[j]):
                self.change_velocities(self.particles[i], self.particles[j])

    def handle_boundary_collisions(self, p):
        """Bounce the particles off the walls elastically."""

        if p.x - p.radius < 0:
            p.x = p.radius
            p.vx = -.95*p.vx
        if p.x + p.radius > 1:
            p.x = 1-p.radius
            p.vx = -.95*p.vx
        if p.y - p.radius < 0:
            p.y = p.radius
            p.vy = -.95*p.vy
        if p.y + p.radius > 1:
            p.y = 1-p.radius
            p.vy = -.95*p.vy
            
        

    def apply_forces(self, p):
        """Override this method to accelerate the particles."""
        if self.srf is None:
            pass
        else:
            x_ind = np.argmin(abs(np.linspace(0, 1, 100) - p.x))
            y_ind = np.argmin(abs(np.linspace(0, 1, 100) - p.y))
            
            #print(p.v, p.vx, p.vy, x_ind, y_ind, p.x, p.y,self.srf.field[0][x_ind, y_ind])
            p.v = p.v + 2*np.array((self.srf.field[0][x_ind, y_ind], self.srf.field[1][x_ind, y_ind]))*(self.dt) #add the velocity of the  #p.vy 
            #print(p.v)
            
    def get_grid_inds(self, p):
        x_ind = np.argmin(abs(np.linspace(0, 1, 100) - p.x))
        y_ind = np.argmin(abs(np.linspace(0, 1, 100) - p.y))
        return x_ind, y_ind        
    def advance_animation(self):
        """Advance the animation by dt, returning the updated Circles list."""

        for i, p in enumerate(self.particles):
           #clean up the eaten food 
            if p.delete:
                self.particles.remove(p)
                self.n -=1
                self.circles[i].radius = 0
                self.circles.pop(i)
            else:   
                p.advance(self.dt)
                #self.handle_boundary_collisions(p)
                self.circles[i].center = p.r
                self.circles[i].radius = p.radius
                
                self.interact(p)
            
        self.handle_collisions()
        return self.circles

    def advance(self):
        """Advance the animation by dt."""
        for i, p in enumerate(self.particles):
            if p.delete:
                self.particles.remove(p)
                self.n -=1
            else:
                p.advance(self.dt)
                self.handle_boundary_collisions(p)
                self.apply_forces(p)
        
        self.handle_collisions()
        

    def init(self):
        """Initialize the Matplotlib animation."""

        self.circles = []
        for particle in self.particles:
            self.circles.append(particle.draw(self.ax))
        return self.circles

    def animate(self, i):
        """The function passed to Matplotlib's FuncAnimation routine."""
        self.ri_ax.cla() # clear the previous image
        self.ri_ax.patch.set_alpha(0.5)
        
        self.ri_ax.plot(np.array(self.particles[0].temp_log) + 0, alpha = .4, c = 'r', label = 'temperature')# plot the line
        self.ri_ax.plot(self.particles[0].food_log, c = 'k', label = 'foodstore')
        self.ri_ax.legend()
        sns.despine(ax = self.ri_ax)
        self.advance_animation()
        return self.circles

    def setup_animation(self):
        self.fig, (self.ri_ax, self.ax) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [1, 5]}, figsize = [8, 10])

        self.srf.plot(fig = self.fig, ax = self.ax)
        
       
        
       
        for s in ['top','bottom','left','right']:
            self.ax.spines[s].set_linewidth(2)
        self.ax.set_aspect('equal', 'box')
        
        #self.ax.set_xlim(0, 1)
        
        #self.ax.set_ylim(0, 1)
        self.ax.xaxis.set_ticks([])
        self.ax.yaxis.set_ticks([])
        
        self.ri_ax.patch.set_alpha(0.1)
        self.ri_ax.xaxis.set_ticks([])
        self.ri_ax.yaxis.set_ticks([])
        
        sns.despine(ax = self.ri_ax)
        sns.despine(ax = self.ax)
    def save_or_show_animation(self, anim, save, filename='collision.mp4'):
        if save:
            Writer = animation.writers['ffmpeg']
            writer = Writer(fps=10, bitrate=1800)
            anim.save(filename, writer=writer)
        else:
            plt.show()


    def do_animation(self, save=False, interval=1, filename='collision.mp4'):
        """Set up and carry out the animation of the molecular dynamics.

        To save the animation as a MP4 movie, set save=True.
        """

        self.setup_animation()
        anim = animation.FuncAnimation(self.fig, self.animate,
                init_func=self.init, frames=200, interval=interval, blit=True)
        self.save_or_show_animation(anim, save, filename)
        return anim
    

class hw1_environment(Simulation):
    #this is our interaction! The environment changes temperature and motion of the particle
    
    def interact(self, p):
            #bounce the particle off the walls
            self.handle_boundary_collisions(p)
            
            #change the temperature of the agent
            x_ind, y_ind = self.get_grid_inds(p)
            
            if hasattr(p, 'temperature'): 
                p.temperature = p.temperature + self.srf.field[x_ind, y_ind]*(self.dt) #add the velocity v
            
            #move faster in high temp regions
            if self.srf.field[x_ind, y_ind] > 0:
                p.v = p.v + .075*self.srf.field[x_ind, y_ind]*self.dt
            if self.srf.field[x_ind, y_ind] < 0:
                p.v = p.v + .01*self.srf.field[x_ind, y_ind]*self.dt    
                
    def advance(self):
        """Advance the animation by dt."""
        for i, p in enumerate(self.particles):
            if p.delete:
                self.particles.remove(p)
                self.n -=1
            else:
                p.advance(self.dt)
                self.interact(p)
        
        self.handle_collisions()
        
#inherits a simulation superclass that deals with animations etc.
#now lets define the code for the environment and the agent! 
#particles have a position and velocity, a temperature, some energy, and other parameters for plotting
class homeostasis_agent(Particle):
    """A class representing a two-dimensional particle."""
    def __init__(self, x = .5, y = .5, vx = 1.1, vy=1.1, radius = .05, styles = {'edgecolor': 'r', 'linewidth': 2, 'alpha': .5} , food_store = 100):
        self.r = np.array((x, y)).astype('float32')
        self.v = np.array((vx, vy)).astype('float32')
        self.radius = radius
        self.mass = self.radius**2
        self.delete = False
        self.styles = styles
        if not self.styles:
            # Default circle styles
            self.styles = {'edgecolor': 'c', 'fill': False}
        self.food_store = food_store
        self.temperature = 98; 
        self.set_point = 98 #homeostatic temp
        self.margin = 2
        
        self.temp_log = []
        self.food_log = []
    
    def monitor(self):
        return self.temperature - self.set_point
    
    def consume(self, dt):
    
        self.food_store -= 1;

        self.temperature += .1
         
    def move(self, dt, boost = 10):
    
        boost = np.random.uniform(-1, 1, size = 2)*boost
        self.v += boost 
        self.r += self.v * dt

        
    def exist(self, dt):
        #we slow down
        self.v = .95*self.v
        
        self.move(dt, boost = 0)
        self.temp_log.append(self.temperature)
        self.food_log.append(self.food_store)
        
        #this means we're dead!
        if self.food_store < 0:
            self.delete = True
        if self.temperature < 85 or self.temperature > 105:
            self.delete = True
            
    def advance(self, dt):
        """Advance the Particle's position forward in time by dt."""
        
        #do basic functions
        self.exist(dt)
        #check internal state
        d_temp = self.monitor()
        
        if d_temp < self.margin:
            self.consume(dt) 
        elif d_temp > self.margin:
            #nothing particle friend can do but move and hope life gets better
            self.move(dt, boost = .5)
            
class hwParticle(homeostasis_agent):
    """A class representing a two-dimensional particle."""
    def __init__(self):
        super().__init__()
        
    def move(self, dt, boost = 1):
        
        #insert your code here to "charge" the agent one unit of food per unit of boost.
        self.food_store -= boost*dt#your code here
        #
        
        boost = np.random.uniform(-1, 1, size = 2)*boost
        self.v += boost 
        self.r += self.v * dt

            
    def advance(self, dt):
        """Advance the Particle's position forward in time by dt."""
        
        #do basic functions
        self.exist(dt)
        #check internal state
        d_temp = self.monitor()
        
        if d_temp < self.margin:
            self.consume(dt) 
        elif d_temp > self.margin:
            #nothing particle friend can do but move and hope life gets better
            self.move(dt, boost = .5)
