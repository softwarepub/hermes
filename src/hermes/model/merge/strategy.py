# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

from ..types.ld_context import iri_map as iri
from .action import Concat, MergeSet
from .match import match_keys, match_person


ACTIONS = {
    "default": MergeSet(match_keys("@id", fall_back_to_equals=True)),
    "merge_match_person": MergeSet(match_person)
}


PROV_STRATEGY = {
    None: {iri["hermes-rt:graph"]: Concat(), iri["hermes-rt:replace"]: Concat(), iri["hermes-rt:reject"]: Concat()}
}

# All troublesome marked entries can contain objects of different types, e.g. Person and Organization.
# This is troublesome because Persons may be compared using a different method than Organizations.

# Filled with entries for every schema-type that can be found inside an JSON-LD dict of type
# SoftwareSourceCode or SoftwareApplication.
CODEMETA_STRATEGY = {None: {None: ACTIONS["default"]}}

CODEMETA_STRATEGY[iri["schema:Thing"]] = {iri["schema:owner"]: None}  # FIXME: troublesome Organization or Person

CODEMETA_STRATEGY[iri["schema:CreativeWork"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:accountablePerson"]: ACTIONS["merge_match_person"],
    iri["schema:audio"]: None,  # FIXME: troublesome AudioObject or Clip or MusicRecording
    iri["schema:author"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:character"]: ACTIONS["merge_match_person"],
    iri["schema:contributor"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:copyrightHolder"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:creator"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:editor"]: ACTIONS["merge_match_person"],
    iri["schema:funder"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:isBasedOn"]: None,  # FIXME: troublesome CreativeWork or Product
    iri["schema:maintainer"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:offers"]: None,  # FIXME: troublesome Demand or Offer
    iri["schema:producer"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:provider"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:publisher"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:sdPublisher"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:size"]: None,  # FIXME: troublesome DefinedTerm or QuantitativeValue or SizeSpecification
    iri["schema:sponsor"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:translator"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:video"]: None  # FIXME: troublesome Clip or VideoObject
}
CODEMETA_STRATEGY[iri["schema:SoftwareSourceCode"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["maintainer"]: ACTIONS["merge_match_person"]
}
CODEMETA_STRATEGY[iri["schema:MediaObject"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:duration"]: None,  # FIXME: troublesome Duration or QuantitativeValue
    iri["schema:height"]: None,  # FIXME: troublesome Distance or QuantitativeValue
    iri["schema:ineligibleRegion"]: None,  # FIXME: troublesome GeoShape or Place
    iri["schema:width"]: None  # FIXME: troublesome Distance or QuantitativeValue
}
CODEMETA_STRATEGY[iri["schema:AudioObject"]] = {**CODEMETA_STRATEGY[iri["schema:MediaObject"]]}
CODEMETA_STRATEGY[iri["schema:ImageObject"]] = {**CODEMETA_STRATEGY[iri["schema:MediaObject"]]}
CODEMETA_STRATEGY[iri["schema:VideoObject"]] = {
    **CODEMETA_STRATEGY[iri["schema:MediaObject"]],
    iri["schema:actor"]: None,  # FIXME: troublesome PerformingGroup or Person
    iri["schema:dircetor"]: ACTIONS["merge_match_person"],
    iri["schema:musicBy"]: None  # FIXME: troublesome MusicGroup or Person
}
CODEMETA_STRATEGY[iri["schema:DataDownload"]] = {**CODEMETA_STRATEGY[iri["schema:MediaObject"]]}
CODEMETA_STRATEGY[iri["schema:Certification"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:Claim"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:claimInterpreter"]: None  # FIXME: troublesome Organization or Person
}
CODEMETA_STRATEGY[iri["schema:Clip"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:actor"]: None,  # FIXME: troublesome PerformingGroup or Person
    iri["schema:dircetor"]: ACTIONS["merge_match_person"],
    iri["schema:musicBy"]: None  # FIXME: troublesome MusicGroup or Person
}
CODEMETA_STRATEGY[iri["schema:Comment"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:parentItem"]: None  # FIXME: troublesome Comment or CreativeWork
}
CODEMETA_STRATEGY[iri["schema:CorrectionComment"]] = {**CODEMETA_STRATEGY[iri["schema:Comment"]]}
CODEMETA_STRATEGY[iri["schema:CreativeWorkSeason"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:actor"]: None  # FIXME: troublesome PerformingGroup or Person
}
CODEMETA_STRATEGY[iri["schema:DefinedTermSet"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:CategoryCodeSet"]] = {**CODEMETA_STRATEGY[iri["schema:DefinedTermSet"]]}
CODEMETA_STRATEGY[iri["schema:Episode"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:actor"]: None,  # FIXME: troublesome PerformingGroup or Person
    iri["schema:dircetor"]: ACTIONS["merge_match_person"],
    iri["schema:duration"]: None,  # FIXME: troublesome Duration or QuantitativeValue
    iri["schema:musicBy"]: None  # FIXME: troublesome MusicGroup or Person
}
CODEMETA_STRATEGY[iri["schema:HowTo"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:step"]: None  # FIXME: troublesome CreativeWork or HowToSection or HowToStep
}
CODEMETA_STRATEGY[iri["schema:HyperTocEntry"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:Map"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:MenuSection"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:MusicRecording"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:byArtist"]: None,  # FIXME: troublesome MusicGroup or Person
    iri["schema:duration"]: None  # FIXME: troublesome Duration or QuantitativeValue
}
CODEMETA_STRATEGY[iri["schema:WebPage"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:reviewedBy"]: None  # FIXME: troublesome Organization or Person
}
CODEMETA_STRATEGY[iri["schema:AboutPage"]] = {**CODEMETA_STRATEGY[iri["schema:WebPage"]]}
CODEMETA_STRATEGY[iri["schema:Article"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:NewsArticle"]] = {**CODEMETA_STRATEGY[iri["schema:Article"]]}
CODEMETA_STRATEGY[iri["schema:ScholarlyArticle"]] = {**CODEMETA_STRATEGY[iri["schema:Article"]]}
CODEMETA_STRATEGY[iri["schema:WebPageElement"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:EducationalOccupationalCredential"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:MusicPlaylist"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:track"]: None  # FIXME: troublesome ItemList or MusicRecording
}
CODEMETA_STRATEGY[iri["schema:MusicAlbum"]] = {
    **CODEMETA_STRATEGY[iri["schema:MusicPlaylist"]],
    iri["schema:byArtist"]: None,  # FIXME: troublesome MusicGroup or Person
}
CODEMETA_STRATEGY[iri["schema:MusicRelease"]] = {
    **CODEMETA_STRATEGY[iri["schema:MusicPlaylist"]],
    iri["schema:creditedTo"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:duration"]: None  # FIXME: troublesome Duration or QuantitativeValue
}
CODEMETA_STRATEGY[iri["schema:MusicComposition"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:composer"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:lyricist"]: ACTIONS["merge_match_person"],
}
CODEMETA_STRATEGY[iri["schema:Photograph"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:Review"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:negativeNotes"]: None,  # FIXME: troublesome ItemList or ListItem or WebContent
    iri["schema:positiveNotes"]: None  # FIXME: troublesome ItemList or ListItem or WebContent
}
CODEMETA_STRATEGY[iri["schema:SoftwareApplication"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:RuntimePlatform"]] = {**CODEMETA_STRATEGY[iri["schema:SoftwareApplication"]]}
CODEMETA_STRATEGY[iri["schema:OperatingSystem"]] = {**CODEMETA_STRATEGY[iri["schema:SoftwareApplication"]]}
CODEMETA_STRATEGY[iri["schema:WebSite"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:WebContent"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:DataCatalog"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:Dataset"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:variableMeasured"]: None  # FIXME: troublesome Property or PropertyValue or StatisticalVariable
}
CODEMETA_STRATEGY[iri["schema:DataFeed"]] = {
    **CODEMETA_STRATEGY[iri["schema:Dataset"]],
    iri["schema:dataFeedElement"]: None  # FIXME: troublesome DataFeedItem or Thing
}

CODEMETA_STRATEGY[iri["schema:Action"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:agent"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:location"]: None,  # FIXME: troublesome Place or PostalAddress or VirtualLocation
    iri["schema:participant"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:provider"]: None  # FIXME: troublesome Organization or Person
}

CODEMETA_STRATEGY[iri["schema:Intangible"]] = {**CODEMETA_STRATEGY[iri["schema:Thing"]]}
CODEMETA_STRATEGY[iri["schema:Rating"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:author"]: None  # FIXME: troublesome Organization or Person
}
CODEMETA_STRATEGY[iri["schema:AggregateRating"]] = {**CODEMETA_STRATEGY[iri["schema:Rating"]]}
CODEMETA_STRATEGY[iri["schema:AlignmentObject"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Audience"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:ComputerLanguage"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Series"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:DefinedTerm"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:CategoryCode"]] = {**CODEMETA_STRATEGY[iri["schema:DefinedTerm"]]}
CODEMETA_STRATEGY[iri["schema:Demand"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:acceptedPaymentMethod"]: None,  # FIXME: troublesome LoanOrCredit or PaymentMethod
    iri["schema:areaServed"]: None,  # FIXME: troublesome AdministrativeArea or GeoShape or Place
    iri["schema:eligibleRegion"]: None,  # FIXME: troublesome GeoShape or Place
    iri["schema:ineligibleRegion"]: None,  # FIXME: troublesome GeoShape or Place
    iri["schema:itemOffered"]: None,  # FIXME: troublesome AggregateOffer or CreativeWork or Event or MenuItem or Product or Service or Trip
    iri["schema:seller"]: None  # FIXME: troublesome Organization or Person
}
CODEMETA_STRATEGY[iri["schema:Offer"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:acceptedPaymentMethod"]: None,  # FIXME: troublesome LoanOrCredit or PaymentMethod
    iri["schema:areaServed"]: None,  # FIXME: troublesome AdministrativeArea or GeoShape or Place
    iri["schema:category"]: None,  # FIXME: troublesome CategoryCode or Thing
    iri["schema:eligibleRegion"]: None,  # FIXME: troublesome GeoShape or Place
    iri["schema:ineligibleRegion"]: None,  # FIXME: troublesome GeoShape or Place
    iri["schema:itemOffered"]: None,  # FIXME: troublesome AggregateOffer or CreativeWork or Event or MenuItem or Product or Service or Trip
    iri["schema:leaseLength"]: None,  # FIXME: troublesome Duration or QuantitativeValue
    iri["schema:offeredBy"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:seller"]: None,  # FIXME: troublesome Organization or Person
}
CODEMETA_STRATEGY[iri["schema:AggregateOffer"]] = {
    **CODEMETA_STRATEGY[iri["schema:Offer"]],
    iri["schema:offers"]: None  # FIXME: troublesome Demand or Offer
}
CODEMETA_STRATEGY[iri["schema:Quantity"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Duration"]] = {**CODEMETA_STRATEGY[iri["schema:Quantity"]]}
CODEMETA_STRATEGY[iri["schema:Energy"]] = {**CODEMETA_STRATEGY[iri["schema:Quantity"]]}
CODEMETA_STRATEGY[iri["schema:Mass"]] = {**CODEMETA_STRATEGY[iri["schema:Quantity"]]}
CODEMETA_STRATEGY[iri["schema:EntryPoint"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:StructuredValue"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:GeoCoordinates"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:GeoShape"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:NutritionInformation"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:MonetaryAmount"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:Distance"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:PostalCodeRangeSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:OpeningHoursSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:RepaymentSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:WarrantyPromise"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:ShippingRateSettings"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:shippingRate"]: None  # FIXME: troublesome MonetaryAmount or ShippingRateSettings
}
CODEMETA_STRATEGY[iri["schema:InteractionCounter"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:interactionService"]: None,  # FIXME: troublesome SoftwareApplication or WebSite
    iri["schema:location"]: None  # FIXME: troublesome Place or PostalAddress or VirtualLocation
}
CODEMETA_STRATEGY[iri["schema:PropertyValue"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:valueReference"]: None  # FIXME: troublesome DefinedTerm or Enumeration or PropertyValue or QualitativeValue or QuantitativeValue or StructuredValue
}
CODEMETA_STRATEGY[iri["schema:ContactPoint"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:areaServed"]: None,  # FIXME: troublesome AdministrativeArea or GeoShape or Place
}
CODEMETA_STRATEGY[iri["schema:PostalAddress"]] = {**CODEMETA_STRATEGY[iri["schema:ContactPoint"]]}
CODEMETA_STRATEGY[iri["schema:OfferShippingDetails"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:depth"]: None,  # FIXME: troublesome Distance or QuantitativeValue
    iri["schema:height"]: None,  # FIXME: troublesome Distance or QuantitativeValue
    iri["schema:shippingRate"]: None,  # FIXME: troublesome MonetaryAmount or ShippingRateSettings
    iri["schema:weight"]: None,  # FIXME: troublesome Mass or QuantitativeValue
    iri["schema:width"]: None  # FIXME: troublesome Distance or QuantitativeValue
}
CODEMETA_STRATEGY[iri["schema:ShippingDeliveryTime"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:handlingTime"]: None,  # FIXME: troublesome QuantitativeValue or ServicePeriod
    iri["schema:transitTime"]: None  # FIXME: troublesome QuantitativeValue or ServicePeriod
}
CODEMETA_STRATEGY[iri["schema:TypeAndQuantityNode"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:typeOfGood"]: None  # FIXME: troublesome Product or Service
}
CODEMETA_STRATEGY[iri["schema:ServicePeriod"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:duration"]: None  # FIXME: troublesome Duration or QuantitativeValue
}
CODEMETA_STRATEGY[iri["schema:QuantitativeValue"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:valueReference"]: None  # FIXME: troublesome DefinedTerm or Enumeration or PropertyValue or QualitativeValue or QuantitativeValue or StructuredValue
}
CODEMETA_STRATEGY[iri["schema:ShippingService"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:handlingTime"]: None  # FIXME: troublesome QuantitativeValue or ServicePeriod
}
CODEMETA_STRATEGY[iri["schema:ShippingConditions"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:depth"]: None,  # FIXME: troublesome Distance or QuantitativeValue
    iri["schema:height"]: None,  # FIXME: troublesome Distance or QuantitativeValue
    iri["schema:shippingRate"]: None,  # FIXME: troublesome MonetaryAmount or ShippingRateSettings
    iri["schema:transitTime"]: None,  # FIXME: troublesome QuantitativeValue or ServicePeriod
    iri["schema:weight"]: None,  # FIXME: troublesome Mass or QuantitativeValue
    iri["schema:width"]: None  # FIXME: troublesome Distance or QuantitativeValue
}
CODEMETA_STRATEGY[iri["schema:QuantitativeValueDistribution"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:duration"]: None  # FIXME: troublesome Duration or QuantitativeValue
}
CODEMETA_STRATEGY[iri["schema:MonetaryAmountDistribution"]] = {
    **CODEMETA_STRATEGY[iri["schema:QuantitativeValueDistribution"]]
}
CODEMETA_STRATEGY[iri["schema:PriceSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:UnitPriceSpecification"]] = {
    **CODEMETA_STRATEGY[iri["schema:PriceSpecification"]],
    iri["schema:billingDuration"]: None,  # FIXME: troublesome Duration or QuantitativeValue
}
CODEMETA_STRATEGY[iri["schema:DeliveryChargeSpecification"]] = {
    **CODEMETA_STRATEGY[iri["schema:PriceSpecification"]],
    iri["schema:areaServed"]: None,  # FIXME: troublesome AdministrativeArea or GeoShape or Place
    iri["schema:eligibleRegion"]: None,  # FIXME: troublesome GeoShape or Place
    iri["schema:ineligibleRegion"]: None  # FIXME: troublesome GeoShape or Place
}
CODEMETA_STRATEGY[iri["schema:LocationFeatureSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:PropertyValue"]]}
CODEMETA_STRATEGY[iri["schema:GeospatialGeometry"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:geoContains"]: None,  # FIXME: troublesome GeospatialGeometry or Place
    iri["schema:geoCoveredBy"]: None,  # FIXME: troublesome GeospatialGeometry or Place
    iri["schema:geoCovers"]: None,  # FIXME: troublesome GeospatialGeometry or Place
    iri["schema:geoCrosses"]: None,  # FIXME: troublesome GeospatialGeometry or Place
    iri["schema:geoDisjoint"]: None,  # FIXME: troublesome GeospatialGeometry or Place
    iri["schema:geoEquals"]: None,  # FIXME: troublesome GeospatialGeometry or Place
    iri["schema:geoIntersects"]: None,  # FIXME: troublesome GeospatialGeometry or Place
    iri["schema:geoOverlaps"]: None,  # FIXME: troublesome GeospatialGeometry or Place
    iri["schema:geoTouches"]: None,  # FIXME: troublesome GeospatialGeometry or Place
    iri["schema:geoWithin"]: None  # FIXME: troublesome GeospatialGeometry or Place
}
CODEMETA_STRATEGY[iri["schema:Grant"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:fundedItem"]: None,  # FIXME: troublesome BioChemEntity or CreativeWork or Event or MedicalEntity or Organization or Person or Product
    iri["schema:funder"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:sponsor"]: None  # FIXME: troublesome Organization or Person
}
CODEMETA_STRATEGY[iri["schema:ItemList"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:itemListElement"]: None  # FIXME: troublesome ListItem or Thing
}
CODEMETA_STRATEGY[iri["schema:OfferCatalog"]] = {**CODEMETA_STRATEGY[iri["schema:ItemList"]]}
CODEMETA_STRATEGY[iri["schema:BreadcrumbList"]] = {**CODEMETA_STRATEGY[iri["schema:ItemList"]]}
CODEMETA_STRATEGY[iri["schema:Language"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Service"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:areaServed"]: None,  # FIXME: troublesome AdministrativeArea or GeoShape or Place
    iri["schema:brand"]: None,  # FIXME: troublesome Brand or Organization
    iri["schema:broker"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:category"]: None,  # FIXME: troublesome CategoryCode or Thing
    iri["schema:isRelatedTo"]: None,  # FIXME: troublesome Product or Service
    iri["schema:isSimilarTo"]: None,  # FIXME: troublesome Product or Service
    iri["schema:offers Demand"]: None,  # FIXME: troublesome or Offer
    iri["schema:provider"]: None  # FIXME: troublesome Organization or Person
}
CODEMETA_STRATEGY[iri["schema:FinancialProduct"]] = {**CODEMETA_STRATEGY[iri["schema:Service"]]}
CODEMETA_STRATEGY[iri["schema:BroadcastService"]] = {**CODEMETA_STRATEGY[iri["schema:Service"]]}
CODEMETA_STRATEGY[iri["schema:CableOrSatelliteService"]] = {**CODEMETA_STRATEGY[iri["schema:Service"]]}
CODEMETA_STRATEGY[iri["schema:LoanOrCredit"]] = {**CODEMETA_STRATEGY[iri["schema:FinancialProduct"]]}
CODEMETA_STRATEGY[iri["schema:MediaSubscription"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Brand"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:HealthInsurancePlan"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:ListItem"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:HowToItem"]] = {**CODEMETA_STRATEGY[iri["schema:ListItem"]]}
CODEMETA_STRATEGY[iri["schema:HowToSupply"]] = {**CODEMETA_STRATEGY[iri["schema:HowToItem"]]}
CODEMETA_STRATEGY[iri["schema:HowToTool"]] = {**CODEMETA_STRATEGY[iri["schema:HowToItem"]]}
CODEMETA_STRATEGY[iri["schema:Enumeration"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:supersededBy"]: None  # FIXME: troublesome Class or Enumeration
}
CODEMETA_STRATEGY[iri["schema:QualitativeValue"]] = {
    **CODEMETA_STRATEGY[iri["schema:Enumeration"]],
    iri["schema:valueReference"]: None  # FIXME: troublesome DefinedTerm or Enumeration or PropertyValue or QualitativeValue or QuantitativeValue or StructuredValue
}
CODEMETA_STRATEGY[iri["schema:SizeSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:QualitativeValue"]]}
CODEMETA_STRATEGY[iri["schema:Class"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:supersededBy"]: None  # FIXME: troublesome Class or Enumeration
}
CODEMETA_STRATEGY[iri["schema:HealthPlanFormulary"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:HealthPlanCostSharingSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:HealthPlanNetwork"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:MemberProgramTier"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:hasTierRequirement"]: None  # FIXME: troublesome CreditCard or MonetaryAmount or UnitPriceSpecification
}
CODEMETA_STRATEGY[iri["schema:MemberProgram"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:MenuItem"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:menuAddOn"]: None,  # FIXME: troublesome MenuItem or MenuSection
    iri["schema:offers"]: None  # FIXME: troublesome Demand or Offer
}
CODEMETA_STRATEGY[iri["schema:MerchantReturnPolicy"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:MerchantReturnPolicySeasonalOverride"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:SpeakableSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:PaymentMethod"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:ProgramMembership"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:member"]: None  # FIXME: troublesome Organization or Person
}
CODEMETA_STRATEGY[iri["schema:Schedule"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:duration"]: None  # FIXME: troublesome Duration or QuantitativeValue
}
CODEMETA_STRATEGY[iri["schema:ServiceChannel"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:VirtualLocation"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Occupation"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:estimatedSalary"]: None  # FIXME: troublesome MonetaryAmount or MonetaryAmountDistribution
}
CODEMETA_STRATEGY[iri["schema:EnergyConsumptionDetails"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:OccupationalExperienceRequirements"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:AlignmentObject"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:BroadcastFrequencySpecification"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:BroadcastChannel"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:ConstraintNode"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:StatisticalVariable"]] = {**CODEMETA_STRATEGY[iri["schema:ConstraintNode"]]}
CODEMETA_STRATEGY[iri["schema:Property"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:supersededBy"]: None,  # FIXME: troublesome Class or Enumeration or Property
}

CODEMETA_STRATEGY[iri["schema:Place"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:geo"]: None,  # FIXME: troublesome GeoCoordinates or GeoShape
    iri["schema:geoContains"]: None,  # FIXME: troublesome GeospatialGeometry or Place
    iri["schema:geoCoveredBy"]: None,  # FIXME: troublesome GeospatialGeometry or Place
    iri["schema:geoCovers"]: None,  # FIXME: troublesome GeospatialGeometry or Place
    iri["schema:geoCrosses"]: None,  # FIXME: troublesome GeospatialGeometry or Place
    iri["schema:geoDisjoint"]: None,  # FIXME: troublesome GeospatialGeometry or Place
    iri["schema:geoEquals"]: None,  # FIXME: troublesome GeospatialGeometry or Place
    iri["schema:geoIntersects"]: None,  # FIXME: troublesome GeospatialGeometry or Place
    iri["schema:geoOverlaps"]: None,  # FIXME: troublesome GeospatialGeometry or Place
    iri["schema:geoTouches"]: None,  # FIXME: troublesome GeospatialGeometry or Place
    iri["schema:geoWithin"]: None,  # FIXME: troublesome GeospatialGeometry or Place
    iri["schema:photo"]: None  # FIXME: troublesome ImageObject or Photograph
}
CODEMETA_STRATEGY[iri["schema:AdministrativeArea"]] = {**CODEMETA_STRATEGY[iri["schema:Place"]]}
CODEMETA_STRATEGY[iri["schema:Country"]] = {**CODEMETA_STRATEGY[iri["schema:AdministrativeArea"]]}
CODEMETA_STRATEGY[iri["schema:CivicStructure"]] = {**CODEMETA_STRATEGY[iri["schema:Place"]]}

CODEMETA_STRATEGY[iri["schema:CreativeWorkSeries"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    **CODEMETA_STRATEGY[iri["schema:Series"]]
}

CODEMETA_STRATEGY[iri["schema:HowToSection"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    **CODEMETA_STRATEGY[iri["schema:ItemList"]],
    **CODEMETA_STRATEGY[iri["schema:ListItem"]]
}
CODEMETA_STRATEGY[iri["schema:HowToStep"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    **CODEMETA_STRATEGY[iri["schema:ItemList"]],
    **CODEMETA_STRATEGY[iri["schema:ListItem"]]
}

CODEMETA_STRATEGY[iri["schema:Event"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:actor"]: None,  # FIXME: troublesome PerformingGroup or Person
    iri["schema:attendee"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:composer"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:contributor"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:dircetor"]: ACTIONS["merge_match_person"],
    iri["schema:duration"]: None,  # FIXME: troublesome Duration or QuantitativeValue
    iri["schema:funder"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:location"]: None,  # FIXME: troublesome Place or PostalAddress or VirtualLocation
    iri["schema:offers"]: None,  # FIXME: troublesome Demand or Offer
    iri["schema:organizer"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:performer"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:sponsor"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:translator"]: None  # FIXME: troublesome Organization or Person
}
CODEMETA_STRATEGY[iri["schema:PublicationEvent"]] = {
    **CODEMETA_STRATEGY[iri["schema:Event"]],
    iri["schema:publishedBy"]: None,  # FIXME: troublesome Organization or Person
}

CODEMETA_STRATEGY[iri["schema:BioChemEntity"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:associatedDisease"]: None,  # FIXME: troublesome MedicalCondition or PropertyValue
    iri["schema:hasMolecularFunction"]: None,  # FIXME: troublesome DefinedTerm or PropertyValue
    iri["schema:isInvolvedInBiologicalProcess"]: None,  # FIXME: troublesome DefinedTerm or PropertyValue
    iri["schema:isLocatedInSubcellularLocation"]: None,  # FIXME: troublesome DefinedTerm or PropertyValue
    iri["schema:taxonomicRange"]: None  # FIXME: troublesome DefinedTerm or Taxon
}
CODEMETA_STRATEGY[iri["schema:Gene"]] = {
    **CODEMETA_STRATEGY[iri["schema:BioChemEntity"]],
    iri["schema:expressedIn"]: None  # FIXME: troublesome AnatomicalStructure or AnatomicalSystem or BioChemEntity or DefinedTerm
}

CODEMETA_STRATEGY[iri["schema:MedicalEntity"]] = {**CODEMETA_STRATEGY[iri["schema:Thing"]]}
CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:DrugLegalStatus"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]]}
CODEMETA_STRATEGY[iri["schema:DDxElement"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]]}
CODEMETA_STRATEGY[iri["schema:MedicalConditionStage"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]]}
CODEMETA_STRATEGY[iri["schema:DrugStrength"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]]}
CODEMETA_STRATEGY[iri["schema:DoseSchedule"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]]}
CODEMETA_STRATEGY[iri["schema:MaximumDoseSchedule"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]]}
CODEMETA_STRATEGY[iri["schema:MedicalGuideline"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:AnatomicalStructure"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:MedicalCause"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:DrugClass"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:LifestyleModification"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:MedicalRiskFactor"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:MedicalTest"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:MedicalDevice"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:MedicalTest"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:MedicalContraindication"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:MedicalProcedure"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:TherapeuticProcedure"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalProcedure"]]}
CODEMETA_STRATEGY[iri["schema:MedicalTherapy"]] = {**CODEMETA_STRATEGY[iri["schema:TherapeuticProcedure"]]}
CODEMETA_STRATEGY[iri["schema:MedicalStudy"]] = {
    **CODEMETA_STRATEGY[iri["schema:MedicalEntity"]],
    iri["schema:sponsor"]: None  # FIXME: troublesome Organization or Person
}
CODEMETA_STRATEGY[iri["schema:MedicalCondition"]] = {
    **CODEMETA_STRATEGY[iri["schema:MedicalEntity"]],
    iri["schema:associatedAnatomy"]: None,  # FIXME: troublesome AnatomicalStructure or AnatomicalSystem or SuperficialAnatomy
    iri["schema:possibleTreatment"]: None,  # FIXME: troublesome Drug or DrugClass or LifestyleModification or MedicalTherapy
    iri["schema:secondaryPrevention"]: None  # FIXME: troublesome Drug or DrugClass or LifestyleModification or MedicalTherapy
}
CODEMETA_STRATEGY[iri["schema:MedicalSignOrSymptom"]] = {
    **CODEMETA_STRATEGY[iri["schema:MedicalCondition"]],
    iri["schema:possibleTreatment"]: None  # FIXME: troublesome Drug or DrugClass or LifestyleModification or MedicalTherapy
}
CODEMETA_STRATEGY[iri["schema:MedicalSign"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalSignOrSymptom"]]}
CODEMETA_STRATEGY[iri["schema:SuperficialAnatomy"]] = {
    **CODEMETA_STRATEGY[iri["schema:MedicalEntity"]],
    iri["schema:relatedAnatomy"]: None  # FIXME: troublesome AnatomicalStructure or AnatomicalSystem
}
CODEMETA_STRATEGY[iri["schema:AnatomicalSystem"]] = {
    **CODEMETA_STRATEGY[iri["schema:MedicalEntity"]],
    iri["schema:comprisedOf"]: None  # FIXME: troublesome AnatomicalStructure or AnatomicalSystem
}

CODEMETA_STRATEGY[iri["schema:MedicalCode"]] = {
    **CODEMETA_STRATEGY[iri["schema:CategoryCode"]],
    **CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]]
}

CODEMETA_STRATEGY[iri["schema:Product"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:brand"]: None,  # FIXME: troublesome Brand or Organization
    iri["schema:category"]: None,  # FIXME: troublesome CategoryCode or Thing
    iri["schema:depth"]: None,  # FIXME: troublesome Distance or QuantitativeValue
    iri["schema:height"]: None,  # FIXME: troublesome Distance or QuantitativeValue
    iri["schema:isRelatedTo"]: None,  # FIXME: troublesome Product or Service
    iri["schema:isSimilarTo"]: None,  # FIXME: troublesome Product or Service
    iri["schema:isVariantOf"]: None,  # FIXME: troublesome ProductGroup or ProductModel
    iri["schema:negativeNotes"]: None,  # FIXME: troublesome ItemList or ListItem or WebContent
    iri["schema:offers"]: None,  # FIXME: troublesome Demand or Offer
    iri["schema:positiveNotes"]: None,  # FIXME: troublesome ItemList or ListItem or WebContent
    iri["schema:size"]: None,  # FIXME: troublesome DefinedTerm or QuantitativeValue or SizeSpecification
    iri["schema:weight"]: None,  # FIXME: troublesome Mass or QuantitativeValue
    iri["schema:width"]: None,  # FIXME: troublesome Distance or QuantitativeValue
}
CODEMETA_STRATEGY[iri["schema:ProductGroup"]] = {**CODEMETA_STRATEGY[iri["schema:Product"]]}
CODEMETA_STRATEGY[iri["schema:Drug"]] = {
    **CODEMETA_STRATEGY[iri["schema:Product"]],
    **CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]
}
CODEMETA_STRATEGY[iri["schema:ProductModel"]] = {
    **CODEMETA_STRATEGY[iri["schema:Product"]],
    iri["schema:isVariantOf"]: None,  # FIXME: troublesome ProductGroup or ProductModel
}

CODEMETA_STRATEGY[iri["schema:PaymentCard"]] = {
    **CODEMETA_STRATEGY[iri["schema:FinancialProduct"]],
    **CODEMETA_STRATEGY[iri["schema:PaymentMethod"]]
}
CODEMETA_STRATEGY[iri["schema:CreditCard"]] = {
    **CODEMETA_STRATEGY[iri["schema:LoanOrCredit"]],
    **CODEMETA_STRATEGY[iri["schema:PaymentCard"]]
}

CODEMETA_STRATEGY[iri["schema:Organization"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:acceptedPaymentMethod"]: None,  # FIXME: troublesome LoanOrCredit or PaymentMethod
    iri["schema:alumni"]: ACTIONS["merge_match_person"],
    iri["schema:areaServed"]: None,  # FIXME: troublesome AdministrativeArea or GeoShape or Place
    iri["schema:brand"]: None,  # FIXME: troublesome Brand or Organization
    iri["schema:employee"]: ACTIONS["merge_match_person"],
    iri["schema:founder"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:funder"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:legalRepresentative"]: ACTIONS["merge_match_person"],
    iri["schema:location"]: None,  # FIXME: troublesome Place or PostalAddress or Text or VirtualLocation
    iri["schema:member"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:memberOf"]: None,  # FIXME: troublesome MemberProgramTier or Organization or ProgramMembership
    iri["schema:ownershipFundingInfo"]: None,  # FIXME: troublesome AboutPage or CreativeWork
    iri["schema:sponsor"]: None  # FIXME: troublesome Organization or Person
}
CODEMETA_STRATEGY[iri["schema:PerformingGroup"]] = {**CODEMETA_STRATEGY[iri["schema:Organization"]]}
CODEMETA_STRATEGY[iri["schema:MusicGroup"]] = {
    **CODEMETA_STRATEGY[iri["schema:PerformingGroup"]],
    iri["schema:musicGroupMember"]: ACTIONS["merge_match_person"],
    iri["schema:track"]: None  # FIXME: troublesome ItemList or MusicRecording
}
CODEMETA_STRATEGY[iri["schema:EducationalOrganization"]] = {
    **CODEMETA_STRATEGY[iri["schema:Organization"]],
    **CODEMETA_STRATEGY[iri["schema:CivicStructure"]]
}

CODEMETA_STRATEGY[iri["schema:DefinedRegion"]] = {
    **CODEMETA_STRATEGY[iri["schema:Place"]],
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]]
}

CODEMETA_STRATEGY[iri["schema:Person"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:alumniOf"]: None,  # FIXME: troublesome EducationalOrganization or Organization
    iri["schema:brand"]: None,  # FIXME: troublesome Brand or Organization
    iri["schema:children"]: ACTIONS["merge_match_person"],
    iri["schema:colleague"]: ACTIONS["merge_match_person"],
    iri["schema:follows"]: ACTIONS["merge_match_person"],
    iri["schema:funder"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:height"]: None,  # FIXME: troublesome Distance or QuantitativeValue
    iri["schema:homeLocation"]: None,  # FIXME: troublesome ContactPoint or Place
    iri["schema:knows"]: ACTIONS["merge_match_person"],
    iri["schema:memberOf"]: None,  # FIXME: troublesome MemberProgramTier or Organization or ProgramMembership
    iri["schema:netWorth"]: None,  # FIXME: troublesome MonetaryAmount or PriceSpecification
    iri["schema:parent"]: ACTIONS["merge_match_person"],
    iri["schema:pronouns"]: None,  # FIXME: troublesome DefinedTerm or StructuredValue
    iri["schema:relatedTo"]: ACTIONS["merge_match_person"],
    iri["schema:sibling"]: ACTIONS["merge_match_person"],
    iri["schema:sponsor"]: None,  # FIXME: troublesome Organization or Person
    iri["schema:spouse"]: ACTIONS["merge_match_person"],
    iri["schema:weight"]: None,  # FIXME: troublesome Mass or QuantitativeValue
    iri["schema:workLocation"]: None  # FIXME: troublesome ContactPoint or Place
}

CODEMETA_STRATEGY[iri["schema:Taxon"]] = {**CODEMETA_STRATEGY[iri["schema:Thing"]]}
