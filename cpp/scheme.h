#ifndef __viscosaur_scheme_h
#define __viscosaur_scheme_h
#include <deal.II/fe/fe_values.h>
namespace dealii
{
    template <int dim> class Function;
    namespace parallel
    {
        namespace distributed
        {
            template <typename T> class Vector;
        }
    }
}
namespace viscosaur
{
    template <int dim> class BoundaryCond;
    template <int dim> class ProblemData;
    template <int dim> class OpFactory;


    #define FE_DEGREE 2
    template <int dim>
    class Scheme
    {
        public:
            virtual void reinit(ProblemData<dim> &p_pd)
            {
                pd = &p_pd;
            }

            OpFactory<dim>* get_tentative_step_factory()
            {
                return this->tent_op_factory;
            }

            OpFactory<dim>* get_correction_step_factory()
            {
                return this->corr_op_factory;
            }

            virtual void get_rhs_grad_terms(
                    dealii::FEValues<dim> &vel_fe_values,
                    Solution<dim> &soln,
                    std::vector<dealii::Tensor<1, dim> >& retval)
            {
                for(int i = 0; i < retval.size(); i++)
                {
                    retval[i] = 0;
                }
            }

            virtual double poisson_rhs_factor() const = 0;
            virtual void handle_poisson_soln(Solution<dim> &soln,
                dealii::PETScWrappers::MPI::Vector& poisson_soln) const
                = 0;     
            virtual BoundaryCond<dim>* handle_bc(BoundaryCond<dim> &bc)
                    const = 0;
            OpFactory<dim>* tent_op_factory;
            OpFactory<dim>* corr_op_factory;
            ProblemData<dim>* pd;
    };

}
#endif
