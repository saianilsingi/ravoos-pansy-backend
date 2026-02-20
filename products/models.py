from django.db import models
from django.core.exceptions import ValidationError


class Category(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=60)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    theme = models.CharField(max_length=30, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "categories"
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "slug"],
                name="unique_slug_per_parent",
            ),
        ]
        indexes = [
            models.Index(fields=["parent"], name="category_parent_idx"),
        ]

    def __str__(self):
        return self.get_full_name()

    def clean(self):
        """Prevent circular references."""
        if self.parent_id and self.pk:
            ancestor = self.parent
            visited = set()
            while ancestor is not None:
                if ancestor.pk == self.pk:
                    raise ValidationError(
                        "A category cannot be its own ancestor."
                    )
                if ancestor.pk in visited:
                    break
                visited.add(ancestor.pk)
                ancestor = ancestor.parent

    def get_ancestors(self):
        """Return list of ancestors from root to direct parent."""
        ancestors = []
        node = self.parent
        while node is not None:
            ancestors.append(node)
            node = node.parent
        ancestors.reverse()
        return ancestors

    def get_breadcrumb(self):
        """Return list of dicts for breadcrumb display: root > ... > self."""
        trail = self.get_ancestors()
        trail.append(self)
        return [
            {"id": c.id, "name": c.name, "slug": c.slug}
            for c in trail
        ]

    def get_full_slug_path(self):
        """Return SEO path like 'clothes/men/shirts'."""
        parts = [a.slug for a in self.get_ancestors()]
        parts.append(self.slug)
        return "/".join(parts)

    def get_full_name(self):
        """Return display name like 'Clothes > Men > Shirts'."""
        parts = [a.name for a in self.get_ancestors()]
        parts.append(self.name)
        return " > ".join(parts)

    def get_descendant_ids(self):
        """
        Return set of IDs for this category + all descendants.
        Iterative BFS — safe for any depth, single query per level.
        """
        ids = {self.pk}
        current_level = {self.pk}
        while current_level:
            children = set(
                Category.objects
                .filter(parent_id__in=current_level, is_active=True)
                .values_list("id", flat=True)
            )
            if not children - ids:
                break
            ids |= children
            current_level = children
        return ids

    @staticmethod
    def resolve_slug_path(slug_path):
        """
        Resolve a full slug path like 'clothes/men/shirts' to a Category.
        Returns None if any segment is invalid.
        """
        slugs = slug_path.strip("/").split("/")
        parent = None
        category = None
        for slug in slugs:
            try:
                category = Category.objects.get(
                    slug=slug, parent=parent, is_active=True
                )
            except Category.DoesNotExist:
                return None
            parent = category
        return category

    @staticmethod
    def get_tree(queryset=None):
        """
        Build nested tree from a flat queryset.
        Single DB query — all categories fetched at once, assembled in Python.
        """
        if queryset is None:
            queryset = Category.objects.filter(is_active=True)

        all_cats = list(
            queryset.select_related("parent").order_by("name")
        )

        by_id = {c.pk: c for c in all_cats}
        for c in all_cats:
            c._children_cache = []

        roots = []
        for c in all_cats:
            if c.parent_id and c.parent_id in by_id:
                by_id[c.parent_id]._children_cache.append(c)
            elif c.parent_id is None:
                roots.append(c)

        return roots


class Product(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
    )
    image = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    stock = models.PositiveIntegerField(default=0)

    # Denormalized rating aggregates — updated by reviews.services.refresh_product_rating()
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(stock__gte=0),
                name="product_stock_non_negative",
            ),
        ]

    def __str__(self):
        return self.name
