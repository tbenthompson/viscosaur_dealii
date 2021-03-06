import viscosaur as vc

class SimpleSolver(object):
    def __init__(self, params, inv_visc, vel_bc, c):
        self.params = params
        self.inv_visc = inv_visc
        self.vel_bc = vel_bc
        self.c = c
        self.pd = vc.ProblemData2D(self.params, self.inv_visc)
        self.soln = vc.Solution2D(self.pd)
        self.scheme = vc.FwdEuler2D(self.pd)
        self.vel_solver = vc.Velocity2D(self.pd, self.soln,
                                        self.vel_bc, self.scheme)
        self.strs_solver = vc.Stress2D(self.pd)

    def step(self, time_step):
        self.soln.start_timestep()
        self.strs_solver.tentative_step(self.soln, self.scheme, time_step)
        self.vel_solver.step(self.soln, self.scheme, time_step)
        self.strs_solver.correction_step(self.soln, self.scheme, time_step)

    def refine(self):
        self.pd.start_refine(self.soln.cur_vel)
        self.soln.start_refine()
        self.pd.execute_refine()
        self.soln.reinit()
        self.soln.post_refine(self.soln)
        self.scheme.reinit(self.pd);
        self.vel_solver.reinit(self.pd, self.soln, self.vel_bc, self.scheme)
        self.strs_solver.reinit(self.pd);

    def initial_adaptive(self, init_strs, init_vel, exact_vel):
        time_step = self.params['time_step'] / self.sub_timesteps
        self.vel_bc.set_t(time_step)
        exact_vel.set_t(time_step)
        for i in range(self.params['initial_adaptive_refines']):
            self.soln.apply_init_cond(init_strs, init_vel)
            self.step(time_step)
            if self.params['output']:
                self.soln.output(self.params['data_dir'], 'init_refinement_' +
                            str(i) + '.', exact_vel)
            self.refine()

    def run(self, init_strs, init_vel, exact_vel):
        self.sub_timesteps = self.params['first_substeps']
        if not self.params["load_mesh"]:
            self.initial_adaptive(init_strs, init_vel, exact_vel)
            self.c.proc0_out("Done with first time step spatial adaptation.")
            self.pd.save_mesh("saved_mesh.msh")

        self.soln.apply_init_cond(init_strs, init_vel)
        self.t = 0
        self.step_index = 1
        self.local_step_index = 1
        while self.t < self.params['t_max']:
            time_step = self.params['time_step'] / self.sub_timesteps
            for sub_t in range(0, self.sub_timesteps):
                self.t += time_step
                self.c.proc0_out("\n\nSolving for time = " + \
                          str(self.t / self.params['secs_in_a_year']) + " \n")
                self.vel_bc.set_t(self.t)
                self.vel_solver.update_bc(self.vel_bc, self.scheme)
                self.step(time_step)
                exact_vel.set_t(self.t)
                filename = "solution_" + str(self.step_index) + "."
                if self.params['output'] and self.step_index % self.params['output_interval'] == 0:
                    self.soln.output(self.params['data_dir'], filename, exact_vel)
                if self.step_index % self.params['refine_interval'] == 0:
                    self.refine()
                    self.pd.save_mesh("saved_mesh.msh")
            if self.local_step_index == 1:
                # At the end of the first time step, we switch to using a BDF2 scheme
                self.sub_timesteps = 1
                self.soln.init_multistep(init_strs, init_vel)
                self.scheme = vc.BDFTwo2D(self.pd)
            self.step_index += 1
            self.local_step_index += 1
            self.after_timestep()
            if self.params['output'] and (self.step_index - 1) % self.params['output_interval'] == 0:
                self.soln.output(self.params['data_dir'], 'after_' + filename, exact_vel)

    def after_timestep(self):
        pass
