from django.db import models


class State(models.Model):
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    boundary = models.JSONField(null=True, blank=True)  # Store as GeoJSON
    center_point = models.JSONField(null=True, blank=True)  # Store as {"type": "Point", "coordinates": [lon, lat]}
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name


class Locality(models.Model):
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='localities')
    boundary = models.JSONField(null=True, blank=True)  # Store as GeoJSON
    center_point = models.JSONField(null=True, blank=True)  # Store as {"type": "Point", "coordinates": [lon, lat]}
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'localities'

    def __str__(self) -> str:
        return f"{self.name}, {self.state.name}"


class Site(models.Model):
    SITE_TYPES = [
        ('gathering', 'Gathering Site'),
        ('camp', 'IDP Camp'),
        ('school', 'School'),
        ('health', 'Health Facility'),
        ('water', 'Water Point'),
        ('other', 'Other'),
    ]
    
    OPERATIONAL_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('planned', 'Planned'),
        ('closed', 'Closed'),
    ]

    # Basic Information
    name = models.CharField(max_length=255, help_text="Site name in English")
    name_ar = models.CharField(max_length=255, blank=True, help_text="Site name in Arabic")
    description = models.TextField(blank=True)
    site_type = models.CharField(max_length=20, choices=SITE_TYPES, default='gathering')
    operational_status = models.CharField(max_length=20, choices=OPERATIONAL_STATUS, default='active', help_text="Current operational status")
    
    # Administrative hierarchy
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='sites', null=True, blank=True)
    locality = models.ForeignKey(Locality, on_delete=models.CASCADE, related_name='sites', null=True, blank=True)
    
    # Location data
    location = models.JSONField(null=True, blank=True)  # Store as {"type": "Point", "coordinates": [lon, lat]}
    size_of_location = models.CharField(max_length=100, blank=True, help_text="Physical size of the location (e.g., '5 hectares', 'Large', 'Small')")
    
    # Population Demographics
    total_population = models.PositiveIntegerField(null=True, blank=True, help_text="Total number of people at the site")
    total_households = models.PositiveIntegerField(null=True, blank=True, help_text="Total number of households/families")
    
    # Age Demographics
    children_under_18 = models.PositiveIntegerField(null=True, blank=True, help_text="Children under 18 years")
    adults_18_59 = models.PositiveIntegerField(null=True, blank=True, help_text="Adults between 18-59 years")
    elderly_60_plus = models.PositiveIntegerField(null=True, blank=True, help_text="Elderly 60+ years")
    
    # Gender Demographics
    male_count = models.PositiveIntegerField(null=True, blank=True, help_text="Total male population")
    female_count = models.PositiveIntegerField(null=True, blank=True, help_text="Total female population")
    
    # Vulnerability Demographics
    disabled_count = models.PositiveIntegerField(null=True, blank=True, help_text="Number of people with disabilities")
    pregnant_women = models.PositiveIntegerField(null=True, blank=True, help_text="Number of pregnant women")
    chronically_ill = models.PositiveIntegerField(null=True, blank=True, help_text="Number of chronically ill people")
    
    # Reporting Information
    report_date = models.DateField(null=True, blank=True, help_text="Date when this data was reported/collected")
    reported_by = models.CharField(max_length=255, blank=True, help_text="Name or organization that reported this data")
    
    # Contact information
    contact_person = models.CharField(max_length=255, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.locality.name}, {self.state.name})"
    
    @property
    def coordinates(self):
        """Return coordinates as [longitude, latitude] if available"""
        if self.location and isinstance(self.location, dict) and 'coordinates' in self.location:
            return self.location['coordinates']
        return None
    
    @property
    def longitude(self):
        """Return longitude"""
        coords = self.coordinates
        return coords[0] if coords else None
    
    @property
    def latitude(self):
        """Return latitude"""
        coords = self.coordinates
        return coords[1] if coords else None
    
    # Demographic calculations
    @property
    def population_by_age_verified(self):
        """Check if age demographics add up to total population"""
        if not all([self.children_under_18, self.adults_18_59, self.elderly_60_plus, self.total_population]):
            return None
        age_total = self.children_under_18 + self.adults_18_59 + self.elderly_60_plus
        return age_total == self.total_population
    
    @property
    def population_by_gender_verified(self):
        """Check if gender demographics add up to total population"""
        if not all([self.male_count, self.female_count, self.total_population]):
            return None
        gender_total = self.male_count + self.female_count
        return gender_total == self.total_population
    
    @property
    def average_household_size(self):
        """Calculate average household size"""
        if self.total_households and self.total_population:
            return round(self.total_population / self.total_households, 2)
        return None
    
    @property
    def vulnerability_rate(self):
        """Calculate percentage of vulnerable population"""
        if not self.total_population:
            return None
        vulnerable_total = (self.disabled_count or 0) + (self.pregnant_women or 0) + (self.chronically_ill or 0)
        return round((vulnerable_total / self.total_population) * 100, 2)
    
    @property
    def child_dependency_ratio(self):
        """Calculate child dependency ratio (children per adult)"""
        adults = (self.adults_18_59 or 0) + (self.elderly_60_plus or 0)
        if adults and self.children_under_18:
            return round(self.children_under_18 / adults, 2)
        return None
