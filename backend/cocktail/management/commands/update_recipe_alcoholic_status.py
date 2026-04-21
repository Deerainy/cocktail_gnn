from django.core.management.base import BaseCommand
from cocktail.models_recipe import Recipe, RecipeBalanceFeature

class Command(BaseCommand):
    help = 'Update recipe is_alcoholic status based on r_base (base spirit presence)'

    def handle(self, *args, **kwargs):
        # 获取所有配方
        recipes = Recipe.objects.all()
        total = recipes.count()
        updated = 0
        
        self.stdout.write(f'Processing {total} recipes...')
        
        for recipe in recipes:
            # 查找配方的balance feature
            try:
                # 获取最新的balance feature记录
                balance_feature = RecipeBalanceFeature.objects.filter(
                    recipe_id=recipe.recipe_id
                ).order_by('-computed_at').first()
                
                # 如果有balance feature且r_base > 0，说明有基酒
                has_alcohol = balance_feature is not None and balance_feature.r_base > 0
            except Exception:
                # 如果出错，默认认为没有酒精
                has_alcohol = False
            
            # 如果状态发生变化，更新配方
            if recipe.is_alcoholic != has_alcohol:
                recipe.is_alcoholic = has_alcohol
                recipe.save()
                updated += 1
        
        self.stdout.write(f'Updated {updated} out of {total} recipes')
        self.stdout.write(self.style.SUCCESS('Task completed successfully!'))