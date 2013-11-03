"""
.. module:: pySART.py
   :platform: Unix
   :synopsis: Implements simultaneous algebraic reconstruction technique for tomographic reconstruction.

.. moduleauthor:: David Vine <djvine@gmail.com>
.. licence:: GPLv2
.. version:: 1.0

""" 


import numpy as np 
import scipy as sp
import scipy.ndimage as spn
from multiprocess import multiprocess, worker
import pdb
import itertools
import time

from matplotlib import rc
from matplotlib import cm
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import matplotlib.pylab as pylab
from matplotlib.pylab import matshow

def split_seq(iterable, size):
	it = iter(iterable)
	item = list(itertools.islice(it, size))
	while item:
		yield item
		item = list(itertools.islice(it, size))

class pysart(object):

	def __init__(self, angles, projections, pslice=None, iterations=50):

		"""
		Projections should be 3D array with order [angle, x, y].
		"""

		self.projections = projections
		self.angles = angles
		self.pslice = pslice
		self.iterations = iterations

		self.n_proj, self.nx, self.ny = projections.shape

		self.reco = sp.zeros((self.ny, self.ny))

		self.relax = 1.0

		self.init_figure()

	def sart(self):
		self.wij_sum = sp.zeros((self.ny, self.ny))

		if self.pslice is None:
			slice_range = range(self.nx)
		else:
			slice_range = [self.pslice]

		for self.pslice in slice_range:
			self.reco = sp.zeros((self.ny, self.ny))
			
			sinogram = self.projections[:,self.pslice,:]
			self.update_figure(pslice=True)
			for it in range(self.iterations):

				self.upd = sp.zeros_like(self.reco)
				for i in range(self.n_proj):
					then = time.time()
					
					multip = multiprocess(self.ray_update_worker, num_processes=12	)
					for chunk in split_seq(range(self.ny), sp.floor(self.ny/multip.num_processes)):
						multip.add_job((self.angles[i], sinogram[i,:], self.reco.copy(), chunk, it==0))
						
					self.do_closeout(multip)
					if i%10==0:
						print 'Iter: {:d}, Proj: {:d}, Duration: {:3.2f} sec'.format(it, i, time.time()-then)

				if it==0:
					self.reco+=self.upd/(self.wij_sum+0.1)
				else:
					self.reco+=self.relax*self.upd/(self.wij_sum+0.1)

				self.update_figure()

	@staticmethod
	@worker
	def ray_update_worker(args):
		angle, p, reco, chunk, calc_wij_sum = args
		upd = sp.zeros_like(reco)
		wij_sum = sp.zeros_like(reco)
		for j in chunk:
			ray = sp.zeros_like(reco)
			ray[:,j]=1
			wij = spn.rotate(ray, angle, reshape=False)
			upd += ((p[j]-sp.sum(wij*reco))/sp.sum(wij**2.0))*wij
			if calc_wij_sum:
				wij_sum+=wij
		if calc_wij_sum:
			return upd, wij_sum
		else:
			return upd, None

	def init_figure(self):
		pylab.ion()

		rc('font', **{'family':'sans-serif', 'sans-serif':['Helvetica']})
		rc('text', usetex=True)

		fig_width_pt = 750

		inches_per_pt = 1.0/72.27
		golden_ratio = (np.sqrt(5.0)-1.0)/2.0

		fig_width_in = fig_width_pt * inches_per_pt
		fig_height_in = fig_width_in * golden_ratio

		fig_dims = [fig_width_in, fig_height_in]

		self.fig = plt.figure(0, figsize=fig_dims)
		self.fig.canvas.set_window_title("pySART: Simultaneous Algebraic Reconstruction Technique")

		self.gs = gridspec.GridSpec(1, 2)
		self.ax1 = plt.subplot(self.gs[0, 0])
		self.ax2 = plt.subplot(self.gs[0, 1])

	def update_figure(self, pslice=False):
		extent = sp.floor(self.ny/np.sqrt(2.0))/2
		self.ax1.cla()
		self.ax1.xaxis.set_major_locator(MaxNLocator(4))
		self.ax1.yaxis.set_major_locator(MaxNLocator(4))
		self.ax1.imshow(self.reco[self.ny/2-extent:self.ny/2+extent, self.ny/2-extent:self.ny/2+extent], cmap=cm.Greys_r)
		self.ax1.set_title('Slice: {:d}'.format(self.pslice))

		if pslice:
			self.ax2.cla()
			self.ax2.xaxis.set_major_locator(MaxNLocator(4))
			self.ax2.yaxis.set_major_locator(MaxNLocator(4))
			self.ax2.imshow(self.projections[:,self.pslice,:], cmap=cm.Greys_r)
			self.ax2.set_title('Sinogram: {:d}'.format(self.pslice))

		pylab.draw()
		pylab.savefig('sart_{:d}.png'.format(self.pslice))
		np.savez('reco_{:d}'.format(self.pslice), self.reco)

	def do_closeout(self, multip):
		for i in range(multip.num_processes):
			multip.jobs.put((None,))

		completed_jobs=0
		res_list = []

		while True:
			if not multip.results.empty():
				upd, wij_sum = multip.results.get()
				self.upd+=upd
				if wij_sum is not None:
					self.wij_sum += wij_sum
				completed_jobs += 1
			if completed_jobs==multip.total_jobs:
				break

		multip.jobs.join()

		multip.jobs.close()
		multip.results.close()

		for process in multip.p:
			process.join()







	