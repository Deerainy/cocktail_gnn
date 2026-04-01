from .models_recipe import RecipeComboAdjustResult, IngredientFlavorAnchor

class ComboAdjustService:
    
    @staticmethod
    def generate_plan_summary(plan):
        target_anchor = IngredientFlavorAnchor.objects.filter(canonical_id=plan.target_canonical_id).first()
        candidate_anchor = IngredientFlavorAnchor.objects.filter(canonical_id=plan.candidate_canonical_id).first()
        
        target_name = target_anchor.canonical_name if target_anchor else plan.target_canonical_id
        candidate_name = candidate_anchor.canonical_name if candidate_anchor else plan.candidate_canonical_id
        
        if plan.repair_role and plan.repair_factor != 1.0:
            return f"替换 {target_name} 为 {candidate_name}，并对 {plan.repair_role} 做局部微调"
        else:
            return f"替换 {target_name} 为 {candidate_name}"
    
    @staticmethod
    def generate_plan_type(plan):
        if plan.repair_role and plan.repair_factor != 1.0:
            return "组合调整"
        else:
            return "单步替代"
    
    @staticmethod
    def generate_trend_tags(plan):
        tags = []
        if plan.delta_sqe_combo > 0:
            tags.append("SQE提升")
        if plan.delta_synergy_combo > 0:
            tags.append("协同增强")
        if plan.delta_conflict_combo < 0:
            tags.append("冲突缓解")
        if plan.delta_balance_combo > 0:
            tags.append("平衡改善")
        return tags if tags else []
    
    @staticmethod
    def generate_stages(plan):
        return {
            'original': plan.old_sqe_total,
            'single_replace': plan.single_sqe_total,
            'combo_adjust': plan.combo_sqe_total
        }
    
    @staticmethod
    def generate_diagnosis(plan):
        diagnosis = []
        
        if plan.delta_sqe_single < 0:
            diagnosis.append("单步替代后SQE下降")
        if plan.delta_synergy_combo > 0:
            diagnosis.append("组合修正后协同项上升")
        if plan.delta_conflict_combo < 0:
            diagnosis.append("组合修正后冲突项下降")
        if plan.delta_balance_combo > 0:
            diagnosis.append("组合修正后平衡项提升")
        
        if not diagnosis:
            diagnosis.append("无明显变化")
        
        return diagnosis
    
    @staticmethod
    def generate_judgement(plan):
        accepted = plan.accept_flag
        diagnosis = ComboAdjustService.generate_diagnosis(plan)
        
        if accepted:
            judgement_text = "该方案在单步替代基础上通过局部比例修正恢复了平衡项，并提升了整体结构质量。"
        else:
            judgement_text = "该方案虽然进行了组合调整，但整体效果未达到接受标准。"
        
        return {
            'accepted': accepted,
            'judgement_text': judgement_text,
            'diagnosis': diagnosis
        }
    
    @staticmethod
    def generate_acceptance_info(plan):
        accepted = plan.accept_flag
        
        if accepted:
            accepted_label = "已接受"
            reason_label = ComboAdjustService._get_reason_label(plan.reason_code)
            reason_text = ComboAdjustService._get_reason_text(plan.reason_code, accepted)
        else:
            accepted_label = "未接受"
            reason_label = ComboAdjustService._get_reason_label(plan.reason_code)
            reason_text = ComboAdjustService._get_reason_text(plan.reason_code, accepted)
        
        return {
            'accept_flag': accepted,
            'accepted_label': accepted_label,
            'reason_label': reason_label,
            'reason_text': reason_text
        }
    
    @staticmethod
    def _get_reason_label(reason_code):
        reason_labels = {
            'STRUCTURE_RECOVERY': '结构恢复有效',
            'BALANCE_IMPROVED': '平衡项改善',
            'SYNERGY_ENHANCED': '协同增强',
            'CONFLICT_REDUCED': '冲突缓解',
            'OVERALL_IMPROVED': '整体提升',
            'INSUFFICIENT_IMPROVEMENT': '改善不足',
            'BALANCE_DEGRADED': '平衡下降',
            'CONFLICT_INCREASED': '冲突增加',
            'STRUCTURE_LOSS': '结构损失',
            'OTHER': '其他原因'
        }
        return reason_labels.get(reason_code, reason_code or '未指定')
    
    @staticmethod
    def _get_reason_text(reason_code, accepted):
        reason_texts = {
            'STRUCTURE_RECOVERY': '组合调整后的整体 SQE 高于原始配方，且局部修正范围有限。',
            'BALANCE_IMPROVED': '组合调整显著改善了平衡项，整体结构更加协调。',
            'SYNERGY_ENHANCED': '组合调整增强了协同关系，提升了整体风味质量。',
            'CONFLICT_REDUCED': '组合调整有效缓解了局部冲突，改善了口感体验。',
            'OVERALL_IMPROVED': '组合调整在多个维度上都有改善，整体效果显著。',
            'INSUFFICIENT_IMPROVEMENT': '组合调整的改善幅度较小，未达到接受标准。',
            'BALANCE_DEGRADED': '组合调整导致平衡项下降，整体结构不够协调。',
            'CONFLICT_INCREASED': '组合调整增加了局部冲突，可能影响口感体验。',
            'STRUCTURE_LOSS': '组合调整引入了结构损失，整体质量下降。',
            'OTHER': '该方案未达到接受标准。'
        }
        
        if accepted:
            return reason_texts.get(reason_code, '该方案已接受。')
        else:
            return reason_texts.get(reason_code, '该方案未达到接受标准。')
    
    @staticmethod
    def generate_step_text(step):
        if step.op_type == 'replace':
            return f"将 {step.target_ingredient} 替换为 {step.candidate_ingredient}"
        elif step.op_type == 'adjust':
            if step.amount_factor:
                return f"对 {step.role_info} 角色进行 ×{step.amount_factor:.2f} 的局部比例调整"
            else:
                return f"对 {step.role_info} 角色进行调整"
        else:
            return step.note or "未知操作"
    
    @staticmethod
    def get_canonical_name(canonical_id):
        anchor = IngredientFlavorAnchor.objects.filter(canonical_id=canonical_id).first()
        return anchor.canonical_name if anchor else canonical_id