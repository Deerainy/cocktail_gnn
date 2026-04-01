from rest_framework.views import APIView
from rest_framework.response import Response
from .models_recipe import (
    Recipe, RecipeIngredient, SqeRecipeScore, RecipeSubstituteResult,
    RecipeComboAdjustResult, RecipeComboAdjustStep
)
from .serializers_recipe import (
    RecipeSerializer, RecipeIngredientSerializer, SqeRecipeScoreSerializer,
    ComboAdjustPlanCardSerializer
)
from .services_combo_adjust import ComboAdjustService

class ComboAdjustOverviewView(APIView):
    def get(self, request, recipe_id):
        try:
            recipe = Recipe.objects.get(recipe_id=recipe_id)
            
            original_ingredients = RecipeIngredient.objects.filter(recipe_id=recipe_id)
            original_sqe = SqeRecipeScore.objects.filter(recipe_id=recipe_id).order_by('-created_at').first()
            
            available_targets = list(RecipeSubstituteResult.objects.filter(
                recipe_id=recipe_id
            ).values_list('target_canonical_id', flat=True).distinct())
            
            total_plans = RecipeComboAdjustResult.objects.filter(recipe_id=recipe_id).count()
            accepted_plans = RecipeComboAdjustResult.objects.filter(
                recipe_id=recipe_id, accept_flag=True
            ).count()
            
            best_plan = RecipeComboAdjustResult.objects.filter(
                recipe_id=recipe_id
            ).order_by('-combo_sqe_total').first()
            
            available_snapshots = list(RecipeComboAdjustResult.objects.filter(
                recipe_id=recipe_id
            ).values_list('snapshot_id', flat=True).distinct())
            
            available_model_versions = list(RecipeComboAdjustResult.objects.filter(
                recipe_id=recipe_id
            ).values_list('model_version', flat=True).distinct())
            
            data = {
                'recipe': RecipeSerializer(recipe).data,
                'original_ingredients': RecipeIngredientSerializer(original_ingredients, many=True).data,
                'original_sqe': SqeRecipeScoreSerializer(original_sqe).data if original_sqe else None,
                'available_targets': available_targets,
                'total_plans': total_plans,
                'accepted_plans': accepted_plans,
                'best_plan_summary': ComboAdjustPlanCardSerializer(best_plan).data if best_plan else None,
                'available_snapshots': available_snapshots,
                'available_model_versions': available_model_versions
            }
            
            return Response({
                "code": 0,
                "message": "ok",
                "data": data
            })
        except Recipe.DoesNotExist:
            return Response({
                "code": 404,
                "message": "recipe not found",
                "data": None
            })
        except Exception as e:
            return Response({
                "code": 500,
                "message": str(e),
                "data": None
            })

class ComboAdjustPlansView(APIView):
    def get(self, request, recipe_id):
        try:
            Recipe.objects.get(recipe_id=recipe_id)
            
            snapshot_id = request.query_params.get('snapshot_id')
            target_canonical_id = request.query_params.get('target_canonical_id')
            accept_flag = request.query_params.get('accept_flag')
            model_version = request.query_params.get('model_version')
            ordering = request.query_params.get('ordering', '-accept_flag,rank_no')
            
            queryset = RecipeComboAdjustResult.objects.filter(recipe_id=recipe_id)
            
            if snapshot_id:
                queryset = queryset.filter(snapshot_id=snapshot_id)
            if target_canonical_id:
                queryset = queryset.filter(target_canonical_id=target_canonical_id)
            if accept_flag is not None:
                queryset = queryset.filter(accept_flag=accept_flag.lower() == 'true')
            if model_version:
                queryset = queryset.filter(model_version=model_version)
            
            if ordering:
                order_fields = ordering.split(',')
                queryset = queryset.order_by(*order_fields)
            
            plans = list(queryset.all())
            serializer = ComboAdjustPlanCardSerializer(plans, many=True)
            
            return Response({
                "code": 0,
                "message": "ok",
                "data": serializer.data
            })
        except Recipe.DoesNotExist:
            return Response({
                "code": 404,
                "message": "recipe not found",
                "data": None
            })
        except Exception as e:
            return Response({
                "code": 500,
                "message": str(e),
                "data": None
            })

class ComboAdjustPlanDetailView(APIView):
    def get(self, request, plan_id):
        try:
            plan = RecipeComboAdjustResult.objects.get(plan_id=plan_id)
            steps = RecipeComboAdjustStep.objects.filter(plan_id=plan_id).order_by('step_no')
            
            data = {
                'plan_id': plan.plan_id,
                'snapshot_id': plan.snapshot_id,
                'recipe_id': plan.recipe_id,
                'target_canonical_id': plan.target_canonical_id,
                'candidate_canonical_id': plan.candidate_canonical_id,
                'repair_canonical_id': plan.repair_canonical_id,
                'repair_role': plan.repair_role,
                'repair_factor': plan.repair_factor,
                'old_sqe_total': plan.old_sqe_total,
                'single_sqe_total': plan.single_sqe_total,
                'combo_sqe_total': plan.combo_sqe_total,
                'delta_sqe_single': plan.delta_sqe_single,
                'delta_sqe_combo': plan.delta_sqe_combo,
                'delta_synergy_combo': plan.delta_synergy_combo,
                'delta_conflict_combo': plan.delta_conflict_combo,
                'delta_balance_combo': plan.delta_balance_combo,
                'accept_flag': plan.accept_flag,
                'reason_code': plan.reason_code,
                'explanation': plan.explanation,
                'plan_json': plan.plan_json,
                'rank_no': plan.rank_no,
                'model_version': plan.model_version,
                'created_at': plan.created_at,
                'updated_at': plan.updated_at,
                'target_canonical': ComboAdjustService.get_canonical_name(plan.target_canonical_id),
                'candidate_canonical': ComboAdjustService.get_canonical_name(plan.candidate_canonical_id),
                'repair_canonical': ComboAdjustService.get_canonical_name(plan.repair_canonical_id) if plan.repair_canonical_id else None,
                'steps': [{
                    'step_id': step.step_id,
                    'step_no': step.step_no,
                    'op_type': step.op_type,
                    'target_ingredient': step.target_ingredient,
                    'target_canonical': step.target_canonical,
                    'candidate_ingredient': step.candidate_ingredient,
                    'candidate_canonical': step.candidate_canonical,
                    'amount_factor': step.amount_factor,
                    'role_info': step.role_info,
                    'before_sqe_total': step.before_sqe_total,
                    'after_sqe_total': step.after_sqe_total,
                    'delta_sqe': step.delta_sqe,
                    'note': step.note,
                    'step_text': ComboAdjustService.generate_step_text(step)
                } for step in steps],
                'judgement': ComboAdjustService.generate_judgement(plan),
                'stages': ComboAdjustService.generate_stages(plan),
                'acceptance_info': ComboAdjustService.generate_acceptance_info(plan)
            }
            
            return Response({
                "code": 0,
                "message": "ok",
                "data": data
            })
        except RecipeComboAdjustResult.DoesNotExist:
            return Response({
                "code": 404,
                "message": "plan not found",
                "data": None
            })
        except Exception as e:
            return Response({
                "code": 500,
                "message": str(e),
                "data": None
            })