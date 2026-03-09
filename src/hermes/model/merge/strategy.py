# SPDX-FileCopyrightText: 2025 German Aerospace Center (DLR)
#
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileContributor: Michael Meinel
# SPDX-FileContributor: Michael Fritzsche

from ..types.ld_context import iri_map as iri
from .action import Concat, MergeSet
from .match import match_keys, match_person, match_multiple_types


DEFAULT_MATCH = match_keys("@id", fall_back_to_equals=True)

MATCH_FUNCTION_FOR_TYPE = {"schema:Person": match_person}

ACTIONS = {
    "default": MergeSet(DEFAULT_MATCH),
    "concat": Concat(),
    "Person": MergeSet(MATCH_FUNCTION_FOR_TYPE["schema:Person"]),
    **{
        "Or".join(types): MergeSet(match_multiple_types(
            *(("schema:" + type, MATCH_FUNCTION_FOR_TYPE.get("schema:" + type, DEFAULT_MATCH)) for type in types)
        ))
        for types in [
            ("AboutPage", "CreativeWork"),
            ("AdministrativeArea", "GeoShape", "Place"),
            ("AggregateOffer", "CreativeWork", "Event", "MenuItem", "Product", "Service", "Trip"),
            ("AnatomicalStructure", "AnatomicalSystem"),
            ("AnatomicalStructure", "AnatomicalSystem", "BioChemEntity", "DefinedTerm"),
            ("AnatomicalStructure", "AnatomicalSystem", "SuperficialAnatomy"),
            ("AudioObject", "Clip", "MusicRecording"),
            ("BioChemEntity", "CreativeWork", "Event", "MedicalEntity", "Organization", "Person", "Product"),
            ("Brand", "Organization"),
            ("CategoryCode", "Thing"),
            ("Class", "Enumeration"),
            ("Class", "Enumeration", "Property"),
            ("Clip", "VideoObject"),
            ("Comment", "CreativeWork"),
            ("ContactPoint", "Place"),
            ("CreativeWork", "HowToSection", "HowToStep"),
            ("CreativeWork", "Product"),
            ("CreditCard", "MonetaryAmount", "UnitPriceSpecification"),
            ("DataFeedItem", "Thing"),
            ("Demand", "Offer"),
            ("DefinedTerm", "Enumeration", "PropertyValue", "QualitativeValue", "QuantitativeValue", "StructuredValue"),
            ("DefinedTerm", "PropertyValue"),
            ("DefinedTerm", "QuantitativeValue", "SizeSpecification"),
            ("DefinedTerm", "StructuredValue"),
            ("DefinedTerm", "Taxon"),
            ("Distance", "QuantitativeValue"),
            ("Drug", "DrugClass", "LifestyleModification", "MedicalTherapy"),
            ("Duration", "QuantitativeValue"),
            ("EducationalOrganization", "Organization"),
            ("GeoCoordinates", "GeoShape"),
            ("GeoShape", "Place"),
            ("GeospatialGeometry", "Place"),
            ("ImageObject", "Photograph"),
            ("ItemList", "ListItem", "WebContent"),
            ("ItemList", "MusicRecording"),
            ("ListItem", "Thing"),
            ("LoanOrCredit", "PaymentMethod"),
            ("Mass", "QuantitativeValue"),
            ("MedicalCondition", "PropertyValue"),
            ("MemberProgramTier", "Organization", "ProgramMembership"),
            ("MenuItem", "MenuSection"),
            ("MonetaryAmount", "MonetaryAmountDistribution"),
            ("MonetaryAmount", "PriceSpecification"),
            ("MonetaryAmount", "ShippingRateSettings"),
            ("MusicGroup", "Person"),
            ("Organization", "Person"),
            ("PerformingGroup", "Person"),
            ("Place", "PostalAddress", "VirtualLocation"),
            ("ProductGroup", "ProductModel"),
            ("Property", "PropertyValue", "StatisticalVariable"),
            ("Product", "Service"),
            ("QuantitativeValue", "ServicePeriod"),
            ("SoftwareApplication", "WebSite")
        ]
    }
}


PROV_STRATEGY = {
    None: {
        iri["hermes-rt:graph"]: ACTIONS["concat"],
        iri["hermes-rt:replace"]: ACTIONS["concat"],
        iri["hermes-rt:reject"]: ACTIONS["concat"]
    }
}


# Filled with entries for every schema-type that can be found inside an JSON-LD dict of type
# SoftwareSourceCode or SoftwareApplication using schema and CodeMeta as Context.
CODEMETA_STRATEGY = {None: {None: ACTIONS["default"]}}
CODEMETA_STRATEGY[iri["schema:Thing"]] = {iri["schema:owner"]: ACTIONS["OrganizationOrPerson"]}


CODEMETA_STRATEGY[iri["schema:Action"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:agent"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:location"]: ACTIONS["PlaceOrPostalAddressOrVirtualLocation"],
    iri["schema:participant"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:provider"]: ACTIONS["OrganizationOrPerson"]
}


CODEMETA_STRATEGY[iri["schema:BioChemEntity"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:associatedDisease"]: ACTIONS["MedicalConditionOrPropertyValue"],
    iri["schema:hasMolecularFunction"]: ACTIONS["DefinedTermOrPropertyValue"],
    iri["schema:isInvolvedInBiologicalProcess"]: ACTIONS["DefinedTermOrPropertyValue"],
    iri["schema:isLocatedInSubcellularLocation"]: ACTIONS["DefinedTermOrPropertyValue"],
    iri["schema:taxonomicRange"]: ACTIONS["DefinedTermOrTaxon"]
}

CODEMETA_STRATEGY[iri["schema:Gene"]] = {
    **CODEMETA_STRATEGY[iri["schema:BioChemEntity"]],
    iri["schema:expressedIn"]: ACTIONS["AnatomicalStructureOrAnatomicalSystemOrBioChemEntityOrDefinedTerm"]
}


CODEMETA_STRATEGY[iri["schema:CreativeWork"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:accountablePerson"]: ACTIONS["Person"],
    iri["schema:audio"]: ACTIONS["AudioObjectOrClipOrMusicRecording"],
    iri["schema:author"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:character"]: ACTIONS["Person"],
    iri["schema:contributor"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:copyrightHolder"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:creator"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:editor"]: ACTIONS["Person"],
    iri["schema:funder"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:isBasedOn"]: ACTIONS["CreativeWorkOrProduct"],
    iri["schema:maintainer"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:offers"]: ACTIONS["DemandOrOffer"],
    iri["schema:producer"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:provider"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:publisher"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:sdPublisher"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:size"]: ACTIONS["DefinedTermOrQuantitativeValueOrSizeSpecification"],
    iri["schema:sponsor"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:translator"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:video"]: ACTIONS["ClipOrVideoObject"]
}

CODEMETA_STRATEGY[iri["schema:Article"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:NewsArticle"]] = {**CODEMETA_STRATEGY[iri["schema:Article"]]}
CODEMETA_STRATEGY[iri["schema:ScholarlyArticle"]] = {**CODEMETA_STRATEGY[iri["schema:Article"]]}
CODEMETA_STRATEGY[iri["schema:Certification"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:Claim"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:claimInterpreter"]: ACTIONS["OrganizationOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:Clip"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:actor"]: ACTIONS["PerformingGroupOrPerson"],
    iri["schema:dircetor"]: ACTIONS["Person"],
    iri["schema:musicBy"]: ACTIONS["MusicGroupOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:Comment"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:parentItem"]: ACTIONS["CommentOrCreativeWork"]
}
CODEMETA_STRATEGY[iri["schema:CorrectionComment"]] = {**CODEMETA_STRATEGY[iri["schema:Comment"]]}
CODEMETA_STRATEGY[iri["schema:CreativeWorkSeason"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:actor"]: ACTIONS["PerformingGroupOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:DataCatalog"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:Dataset"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:variableMeasured"]: ACTIONS["PropertyOrPropertyValueOrStatisticalVariable"]
}
CODEMETA_STRATEGY[iri["schema:DataFeed"]] = {
    **CODEMETA_STRATEGY[iri["schema:Dataset"]],
    iri["schema:dataFeedElement"]: ACTIONS["DataFeedItemOrThing"]
}
CODEMETA_STRATEGY[iri["schema:DefinedTermSet"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:CategoryCodeSet"]] = {**CODEMETA_STRATEGY[iri["schema:DefinedTermSet"]]}
CODEMETA_STRATEGY[iri["schema:EducationalOccupationalCredential"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:Episode"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:actor"]: ACTIONS["PerformingGroupOrPerson"],
    iri["schema:dircetor"]: ACTIONS["Person"],
    iri["schema:duration"]: ACTIONS["DurationOrQuantitativeValue"],
    iri["schema:musicBy"]: ACTIONS["MusicGroupOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:HowTo"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:step"]: ACTIONS["CreativeWorkOrHowToSectionOrHowToStep"]
}
CODEMETA_STRATEGY[iri["schema:HyperTocEntry"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:Map"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:MediaObject"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:duration"]: ACTIONS["DurationOrQuantitativeValue"],
    iri["schema:height"]: ACTIONS["DistanceOrQuantitativeValue"],
    iri["schema:ineligibleRegion"]: ACTIONS["GeoShapeOrPlace"],
    iri["schema:width"]: ACTIONS["DistanceOrQuantitativeValue"]
}
CODEMETA_STRATEGY[iri["schema:AudioObject"]] = {**CODEMETA_STRATEGY[iri["schema:MediaObject"]]}
CODEMETA_STRATEGY[iri["schema:DataDownload"]] = {**CODEMETA_STRATEGY[iri["schema:MediaObject"]]}
CODEMETA_STRATEGY[iri["schema:ImageObject"]] = {**CODEMETA_STRATEGY[iri["schema:MediaObject"]]}
CODEMETA_STRATEGY[iri["schema:VideoObject"]] = {
    **CODEMETA_STRATEGY[iri["schema:MediaObject"]],
    iri["schema:actor"]: ACTIONS["PerformingGroupOrPerson"],
    iri["schema:dircetor"]: ACTIONS["Person"],
    iri["schema:musicBy"]: ACTIONS["MusicGroupOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:MenuSection"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:MusicComposition"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:composer"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:lyricist"]: ACTIONS["Person"]
}
CODEMETA_STRATEGY[iri["schema:MusicPlaylist"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:track"]: ACTIONS["ItemListOrMusicRecording"]
}
CODEMETA_STRATEGY[iri["schema:MusicAlbum"]] = {
    **CODEMETA_STRATEGY[iri["schema:MusicPlaylist"]],
    iri["schema:byArtist"]: ACTIONS["MusicGroupOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:MusicRelease"]] = {
    **CODEMETA_STRATEGY[iri["schema:MusicPlaylist"]],
    iri["schema:creditedTo"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:duration"]: ACTIONS["DurationOrQuantitativeValue"]
}
CODEMETA_STRATEGY[iri["schema:MusicRecording"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:byArtist"]: ACTIONS["MusicGroupOrPerson"],
    iri["schema:duration"]: ACTIONS["DurationOrQuantitativeValue"]
}
CODEMETA_STRATEGY[iri["schema:Photograph"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:Review"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:negativeNotes"]: ACTIONS["ItemListOrListItemOrWebContent"],
    iri["schema:positiveNotes"]: ACTIONS["ItemListOrListItemOrWebContent"]
}
CODEMETA_STRATEGY[iri["schema:SoftwareApplication"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:OperatingSystem"]] = {**CODEMETA_STRATEGY[iri["schema:SoftwareApplication"]]}
CODEMETA_STRATEGY[iri["schema:RuntimePlatform"]] = {**CODEMETA_STRATEGY[iri["schema:SoftwareApplication"]]}
CODEMETA_STRATEGY[iri["schema:SoftwareSourceCode"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["maintainer"]: ACTIONS["Person"]
}
CODEMETA_STRATEGY[iri["schema:WebContent"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:WebPage"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    iri["schema:reviewedBy"]: ACTIONS["OrganizationOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:AboutPage"]] = {**CODEMETA_STRATEGY[iri["schema:WebPage"]]}
CODEMETA_STRATEGY[iri["schema:WebPageElement"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}
CODEMETA_STRATEGY[iri["schema:WebSite"]] = {**CODEMETA_STRATEGY[iri["schema:CreativeWork"]]}


CODEMETA_STRATEGY[iri["schema:Event"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:actor"]: ACTIONS["PerformingGroupOrPerson"],
    iri["schema:attendee"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:composer"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:contributor"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:dircetor"]: ACTIONS["Person"],
    iri["schema:duration"]: ACTIONS["DurationOrQuantitativeValue"],
    iri["schema:funder"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:location"]: ACTIONS["PlaceOrPostalAddressOrVirtualLocation"],
    iri["schema:offers"]: ACTIONS["DemandOrOffer"],
    iri["schema:organizer"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:performer"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:sponsor"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:translator"]: ACTIONS["OrganizationOrPerson"]
}

CODEMETA_STRATEGY[iri["schema:PublicationEvent"]] = {
    **CODEMETA_STRATEGY[iri["schema:Event"]],
    iri["schema:publishedBy"]: ACTIONS["OrganizationOrPerson"]
}


CODEMETA_STRATEGY[iri["schema:Intangible"]] = {**CODEMETA_STRATEGY[iri["schema:Thing"]]}

CODEMETA_STRATEGY[iri["schema:AlignmentObject"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Audience"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Brand"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:BroadcastChannel"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:BroadcastFrequencySpecification"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Class"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:supersededBy"]: ACTIONS["ClassOrEnumeration"]
}
CODEMETA_STRATEGY[iri["schema:ComputerLanguage"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:ConstraintNode"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:StatisticalVariable"]] = {**CODEMETA_STRATEGY[iri["schema:ConstraintNode"]]}
CODEMETA_STRATEGY[iri["schema:DefinedTerm"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:CategoryCode"]] = {**CODEMETA_STRATEGY[iri["schema:DefinedTerm"]]}
CODEMETA_STRATEGY[iri["schema:Demand"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:acceptedPaymentMethod"]: ACTIONS["LoanOrCreditOrPaymentMethod"],
    iri["schema:areaServed"]: ACTIONS["AdministrativeAreaOrGeoShapeOrPlace"],
    iri["schema:eligibleRegion"]: ACTIONS["GeoShapeOrPlace"],
    iri["schema:ineligibleRegion"]: ACTIONS["GeoShapeOrPlace"],
    iri["schema:itemOffered"]: ACTIONS["AggregateOfferOrCreativeWorkOrEventOrMenuItemOrProductOrServiceOrTrip"],
    iri["schema:seller"]: ACTIONS["OrganizationOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:EnergyConsumptionDetails"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:EntryPoint"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Enumeration"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:supersededBy"]: ACTIONS["ClassOrEnumeration"]
}
CODEMETA_STRATEGY[iri["schema:QualitativeValue"]] = {
    **CODEMETA_STRATEGY[iri["schema:Enumeration"]],
    iri[
        "schema:valueReference"
    ]: ACTIONS["DefinedTermOrEnumerationOrPropertyValueOrQualitativeValueOrQuantitativeValueOrStructuredValue"]
}
CODEMETA_STRATEGY[iri["schema:SizeSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:QualitativeValue"]]}
CODEMETA_STRATEGY[iri["schema:GeospatialGeometry"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:geoContains"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoCoveredBy"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoCovers"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoCrosses"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoDisjoint"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoEquals"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoIntersects"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoOverlaps"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoTouches"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoWithin"]: ACTIONS["GeospatialGeometryOrPlace"]
}
CODEMETA_STRATEGY[iri["schema:Grant"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri[
        "schema:fundedItem"
    ]: ACTIONS["BioChemEntityOrCreativeWorkOrEventOrMedicalEntityOrOrganizationOrPersonOrProduct"],
    iri["schema:funder"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:sponsor"]: ACTIONS["OrganizationOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:HealthInsurancePlan"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:HealthPlanCostSharingSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:HealthPlanFormulary"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:HealthPlanNetwork"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:ItemList"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:itemListElement"]: ACTIONS["ListItemOrThing"]
}
CODEMETA_STRATEGY[iri["schema:OfferCatalog"]] = {**CODEMETA_STRATEGY[iri["schema:ItemList"]]}
CODEMETA_STRATEGY[iri["schema:BreadcrumbList"]] = {**CODEMETA_STRATEGY[iri["schema:ItemList"]]}
CODEMETA_STRATEGY[iri["schema:Language"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:ListItem"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:HowToItem"]] = {**CODEMETA_STRATEGY[iri["schema:ListItem"]]}
CODEMETA_STRATEGY[iri["schema:HowToSupply"]] = {**CODEMETA_STRATEGY[iri["schema:HowToItem"]]}
CODEMETA_STRATEGY[iri["schema:HowToTool"]] = {**CODEMETA_STRATEGY[iri["schema:HowToItem"]]}
CODEMETA_STRATEGY[iri["schema:MediaSubscription"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:MemberProgram"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:MemberProgramTier"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:hasTierRequirement"]: ACTIONS["CreditCardOrMonetaryAmountOrUnitPriceSpecification"]
}
CODEMETA_STRATEGY[iri["schema:MenuItem"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:menuAddOn"]: ACTIONS["MenuItemOrMenuSection"],
    iri["schema:offers"]: ACTIONS["DemandOrOffer"]
}
CODEMETA_STRATEGY[iri["schema:MerchantReturnPolicy"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:MerchantReturnPolicySeasonalOverride"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Occupation"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:estimatedSalary"]: ACTIONS["MonetaryAmountOrMonetaryAmountDistribution"]
}
CODEMETA_STRATEGY[iri["schema:OccupationalExperienceRequirements"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Offer"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:acceptedPaymentMethod"]: ACTIONS["LoanOrCreditOrPaymentMethod"],
    iri["schema:areaServed"]: ACTIONS["AdministrativeAreaOrGeoShapeOrPlace"],
    iri["schema:category"]: ACTIONS["CategoryCodeOrThing"],
    iri["schema:eligibleRegion"]: ACTIONS["GeoShapeOrPlace"],
    iri["schema:ineligibleRegion"]: ACTIONS["GeoShapeOrPlace"],
    iri["schema:itemOffered"]: ACTIONS["AggregateOfferOrCreativeWorkOrEventOrMenuItemOrProductOrServiceOrTrip"],
    iri["schema:leaseLength"]: ACTIONS["DurationOrQuantitativeValue"],
    iri["schema:offeredBy"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:seller"]: ACTIONS["OrganizationOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:AggregateOffer"]] = {
    **CODEMETA_STRATEGY[iri["schema:Offer"]],
    iri["schema:offers"]: ACTIONS["DemandOrOffer"]
}
CODEMETA_STRATEGY[iri["schema:PaymentMethod"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:ProgramMembership"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:member"]: ACTIONS["OrganizationOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:Property"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:supersededBy"]: ACTIONS["ClassOrEnumerationOrProperty"]
}
CODEMETA_STRATEGY[iri["schema:Quantity"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Duration"]] = {**CODEMETA_STRATEGY[iri["schema:Quantity"]]}
CODEMETA_STRATEGY[iri["schema:Energy"]] = {**CODEMETA_STRATEGY[iri["schema:Quantity"]]}
CODEMETA_STRATEGY[iri["schema:Mass"]] = {**CODEMETA_STRATEGY[iri["schema:Quantity"]]}
CODEMETA_STRATEGY[iri["schema:Rating"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:author"]: ACTIONS["OrganizationOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:AggregateRating"]] = {**CODEMETA_STRATEGY[iri["schema:Rating"]]}
CODEMETA_STRATEGY[iri["schema:Schedule"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:duration"]: ACTIONS["DurationOrQuantitativeValue"]
}
CODEMETA_STRATEGY[iri["schema:Series"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:Service"]] = {
    **CODEMETA_STRATEGY[iri["schema:Intangible"]],
    iri["schema:areaServed"]: ACTIONS["AdministrativeAreaOrGeoShapeOrPlace"],
    iri["schema:brand"]: ACTIONS["BrandOrOrganization"],
    iri["schema:broker"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:category"]: ACTIONS["CategoryCodeOrThing"],
    iri["schema:isRelatedTo"]: ACTIONS["ProductOrService"],
    iri["schema:isSimilarTo"]: ACTIONS["ProductOrService"],
    iri["schema:offers"]: ACTIONS["DemandOrOffer"],
    iri["schema:provider"]: ACTIONS["OrganizationOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:BroadcastService"]] = {**CODEMETA_STRATEGY[iri["schema:Service"]]}
CODEMETA_STRATEGY[iri["schema:CableOrSatelliteService"]] = {**CODEMETA_STRATEGY[iri["schema:Service"]]}
CODEMETA_STRATEGY[iri["schema:FinancialProduct"]] = {**CODEMETA_STRATEGY[iri["schema:Service"]]}
CODEMETA_STRATEGY[iri["schema:LoanOrCredit"]] = {**CODEMETA_STRATEGY[iri["schema:FinancialProduct"]]}
CODEMETA_STRATEGY[iri["schema:ServiceChannel"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:SpeakableSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:StructuredValue"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}
CODEMETA_STRATEGY[iri["schema:ContactPoint"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:areaServed"]: ACTIONS["AdministrativeAreaOrGeoShapeOrPlace"]
}
CODEMETA_STRATEGY[iri["schema:PostalAddress"]] = {**CODEMETA_STRATEGY[iri["schema:ContactPoint"]]}
CODEMETA_STRATEGY[iri["schema:Distance"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:GeoCoordinates"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:GeoShape"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:InteractionCounter"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:interactionService"]: ACTIONS["SoftwareApplicationOrWebSite"],
    iri["schema:location"]: ACTIONS["PlaceOrPostalAddressOrVirtualLocation"]
}
CODEMETA_STRATEGY[iri["schema:MonetaryAmount"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:NutritionInformation"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:OfferShippingDetails"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:depth"]: ACTIONS["DistanceOrQuantitativeValue"],
    iri["schema:height"]: ACTIONS["DistanceOrQuantitativeValue"],
    iri["schema:shippingRate"]: ACTIONS["MonetaryAmountOrShippingRateSettings"],
    iri["schema:weight"]: ACTIONS["MassOrQuantitativeValue"],
    iri["schema:width"]: ACTIONS["DistanceOrQuantitativeValue"]
}
CODEMETA_STRATEGY[iri["schema:OpeningHoursSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:PostalCodeRangeSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:PriceSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:DeliveryChargeSpecification"]] = {
    **CODEMETA_STRATEGY[iri["schema:PriceSpecification"]],
    iri["schema:areaServed"]: ACTIONS["AdministrativeAreaOrGeoShapeOrPlace"],
    iri["schema:eligibleRegion"]: ACTIONS["GeoShapeOrPlace"],
    iri["schema:ineligibleRegion"]: ACTIONS["GeoShapeOrPlace"]
}
CODEMETA_STRATEGY[iri["schema:UnitPriceSpecification"]] = {
    **CODEMETA_STRATEGY[iri["schema:PriceSpecification"]],
    iri["schema:billingDuration"]: ACTIONS["DurationOrQuantitativeValue"]
}
CODEMETA_STRATEGY[iri["schema:PropertyValue"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri[
        "schema:valueReference"
    ]: ACTIONS["DefinedTermOrEnumerationOrPropertyValueOrQualitativeValueOrQuantitativeValueOrStructuredValue"]
}
CODEMETA_STRATEGY[iri["schema:LocationFeatureSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:PropertyValue"]]}
CODEMETA_STRATEGY[iri["schema:QuantitativeValue"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri[
        "schema:valueReference"
    ]: ACTIONS["DefinedTermOrEnumerationOrPropertyValueOrQualitativeValueOrQuantitativeValueOrStructuredValue"]
}
CODEMETA_STRATEGY[iri["schema:QuantitativeValueDistribution"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:duration"]: ACTIONS["DurationOrQuantitativeValue"]
}
CODEMETA_STRATEGY[iri["schema:MonetaryAmountDistribution"]] = {
    **CODEMETA_STRATEGY[iri["schema:QuantitativeValueDistribution"]]
}
CODEMETA_STRATEGY[iri["schema:RepaymentSpecification"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:ServicePeriod"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:duration"]: ACTIONS["DurationOrQuantitativeValue"]
}
CODEMETA_STRATEGY[iri["schema:ShippingConditions"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:depth"]: ACTIONS["DistanceOrQuantitativeValue"],
    iri["schema:height"]: ACTIONS["DistanceOrQuantitativeValue"],
    iri["schema:shippingRate"]: ACTIONS["MonetaryAmountOrShippingRateSettings"],
    iri["schema:transitTime"]: ACTIONS["QuantitativeValueOrServicePeriod"],
    iri["schema:weight"]: ACTIONS["MassOrQuantitativeValue"],
    iri["schema:width"]: ACTIONS["DistanceOrQuantitativeValue"]
}
CODEMETA_STRATEGY[iri["schema:ShippingDeliveryTime"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:handlingTime"]: ACTIONS["QuantitativeValueOrServicePeriod"],
    iri["schema:transitTime"]: ACTIONS["QuantitativeValueOrServicePeriod"]
}
CODEMETA_STRATEGY[iri["schema:ShippingRateSettings"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:shippingRate"]: ACTIONS["MonetaryAmountOrShippingRateSettings"]
}
CODEMETA_STRATEGY[iri["schema:ShippingService"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:handlingTime"]: ACTIONS["QuantitativeValueOrServicePeriod"]
}
CODEMETA_STRATEGY[iri["schema:TypeAndQuantityNode"]] = {
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]],
    iri["schema:typeOfGood"]: ACTIONS["ProductOrService"]
}
CODEMETA_STRATEGY[iri["schema:WarrantyPromise"]] = {**CODEMETA_STRATEGY[iri["schema:StructuredValue"]]}
CODEMETA_STRATEGY[iri["schema:VirtualLocation"]] = {**CODEMETA_STRATEGY[iri["schema:Intangible"]]}


CODEMETA_STRATEGY[iri["schema:MedicalEntity"]] = {**CODEMETA_STRATEGY[iri["schema:Thing"]]}

CODEMETA_STRATEGY[iri["schema:AnatomicalStructure"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:AnatomicalSystem"]] = {
    **CODEMETA_STRATEGY[iri["schema:MedicalEntity"]],
    iri["schema:comprisedOf"]: ACTIONS["AnatomicalStructureOrAnatomicalSystem"]
}
CODEMETA_STRATEGY[iri["schema:DrugClass"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:LifestyleModification"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:MedicalCause"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:MedicalCondition"]] = {
    **CODEMETA_STRATEGY[iri["schema:MedicalEntity"]],
    iri["schema:associatedAnatomy"]: ACTIONS["AnatomicalStructureOrAnatomicalSystemOrSuperficialAnatomy"],
    iri["schema:possibleTreatment"]: ACTIONS["DrugOrDrugClassOrLifestyleModificationOrMedicalTherapy"],
    iri["schema:secondaryPrevention"]: ACTIONS["DrugOrDrugClassOrLifestyleModificationOrMedicalTherapy"]
}
CODEMETA_STRATEGY[iri["schema:MedicalSignOrSymptom"]] = {
    **CODEMETA_STRATEGY[iri["schema:MedicalCondition"]],
    iri["schema:possibleTreatment"]: ACTIONS["DrugOrDrugClassOrLifestyleModificationOrMedicalTherapy"]
}
CODEMETA_STRATEGY[iri["schema:MedicalSign"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalSignOrSymptom"]]}
CODEMETA_STRATEGY[iri["schema:MedicalContraindication"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:MedicalDevice"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:MedicalGuideline"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:DDxElement"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]]}
CODEMETA_STRATEGY[iri["schema:DrugLegalStatus"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]]}
CODEMETA_STRATEGY[iri["schema:DoseSchedule"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]]}
CODEMETA_STRATEGY[iri["schema:DrugStrength"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]]}
CODEMETA_STRATEGY[iri["schema:MaximumDoseSchedule"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]]}
CODEMETA_STRATEGY[iri["schema:MedicalConditionStage"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]]}
CODEMETA_STRATEGY[iri["schema:MedicalProcedure"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:TherapeuticProcedure"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalProcedure"]]}
CODEMETA_STRATEGY[iri["schema:MedicalTherapy"]] = {**CODEMETA_STRATEGY[iri["schema:TherapeuticProcedure"]]}
CODEMETA_STRATEGY[iri["schema:MedicalRiskFactor"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:MedicalStudy"]] = {
    **CODEMETA_STRATEGY[iri["schema:MedicalEntity"]],
    iri["schema:sponsor"]: ACTIONS["OrganizationOrPerson"]
}
CODEMETA_STRATEGY[iri["schema:MedicalTest"]] = {**CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]}
CODEMETA_STRATEGY[iri["schema:SuperficialAnatomy"]] = {
    **CODEMETA_STRATEGY[iri["schema:MedicalEntity"]],
    iri["schema:relatedAnatomy"]: ACTIONS["AnatomicalStructureOrAnatomicalSystem"]
}


CODEMETA_STRATEGY[iri["schema:Organization"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:acceptedPaymentMethod"]: ACTIONS["LoanOrCreditOrPaymentMethod"],
    iri["schema:alumni"]: ACTIONS["Person"],
    iri["schema:areaServed"]: ACTIONS["AdministrativeAreaOrGeoShapeOrPlace"],
    iri["schema:brand"]: ACTIONS["BrandOrOrganization"],
    iri["schema:employee"]: ACTIONS["Person"],
    iri["schema:founder"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:funder"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:legalRepresentative"]: ACTIONS["Person"],
    iri["schema:location"]: ACTIONS["PlaceOrPostalAddressOrVirtualLocation"],
    iri["schema:member"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:memberOf"]: ACTIONS["MemberProgramTierOrOrganizationOrProgramMembership"],
    iri["schema:ownershipFundingInfo"]: ACTIONS["AboutPageOrCreativeWork"],
    iri["schema:sponsor"]: ACTIONS["OrganizationOrPerson"]
}

CODEMETA_STRATEGY[iri["schema:PerformingGroup"]] = {**CODEMETA_STRATEGY[iri["schema:Organization"]]}
CODEMETA_STRATEGY[iri["schema:MusicGroup"]] = {
    **CODEMETA_STRATEGY[iri["schema:PerformingGroup"]],
    iri["schema:musicGroupMember"]: ACTIONS["Person"],
    iri["schema:track"]: ACTIONS["ItemListOrMusicRecording"]
}


CODEMETA_STRATEGY[iri["schema:Person"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:alumniOf"]: ACTIONS["EducationalOrganizationOrOrganization"],
    iri["schema:brand"]: ACTIONS["BrandOrOrganization"],
    iri["schema:children"]: ACTIONS["Person"],
    iri["schema:colleague"]: ACTIONS["Person"],
    iri["schema:follows"]: ACTIONS["Person"],
    iri["schema:funder"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:height"]: ACTIONS["DistanceOrQuantitativeValue"],
    iri["schema:homeLocation"]: ACTIONS["ContactPointOrPlace"],
    iri["schema:knows"]: ACTIONS["Person"],
    iri["schema:memberOf"]: ACTIONS["MemberProgramTierOrOrganizationOrProgramMembership"],
    iri["schema:netWorth"]: ACTIONS["MonetaryAmountOrPriceSpecification"],
    iri["schema:parent"]: ACTIONS["Person"],
    iri["schema:pronouns"]: ACTIONS["DefinedTermOrStructuredValue"],
    iri["schema:relatedTo"]: ACTIONS["Person"],
    iri["schema:sibling"]: ACTIONS["Person"],
    iri["schema:sponsor"]: ACTIONS["OrganizationOrPerson"],
    iri["schema:spouse"]: ACTIONS["Person"],
    iri["schema:weight"]: ACTIONS["MassOrQuantitativeValue"],
    iri["schema:workLocation"]: ACTIONS["ContactPointOrPlace"]
}


CODEMETA_STRATEGY[iri["schema:Place"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:geo"]: ACTIONS["GeoCoordinatesOrGeoShape"],
    iri["schema:geoContains"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoCoveredBy"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoCovers"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoCrosses"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoDisjoint"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoEquals"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoIntersects"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoOverlaps"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoTouches"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:geoWithin"]: ACTIONS["GeospatialGeometryOrPlace"],
    iri["schema:photo"]: ACTIONS["ImageObjectOrPhotograph"]
}

CODEMETA_STRATEGY[iri["schema:AdministrativeArea"]] = {**CODEMETA_STRATEGY[iri["schema:Place"]]}
CODEMETA_STRATEGY[iri["schema:Country"]] = {**CODEMETA_STRATEGY[iri["schema:AdministrativeArea"]]}
CODEMETA_STRATEGY[iri["schema:CivicStructure"]] = {**CODEMETA_STRATEGY[iri["schema:Place"]]}


CODEMETA_STRATEGY[iri["schema:Product"]] = {
    **CODEMETA_STRATEGY[iri["schema:Thing"]],
    iri["schema:brand"]: ACTIONS["BrandOrOrganization"],
    iri["schema:category"]: ACTIONS["CategoryCodeOrThing"],
    iri["schema:depth"]: ACTIONS["DistanceOrQuantitativeValue"],
    iri["schema:height"]: ACTIONS["DistanceOrQuantitativeValue"],
    iri["schema:isRelatedTo"]: ACTIONS["ProductOrService"],
    iri["schema:isSimilarTo"]: ACTIONS["ProductOrService"],
    iri["schema:isVariantOf"]: ACTIONS["ProductGroupOrProductModel"],
    iri["schema:negativeNotes"]: ACTIONS["ItemListOrListItemOrWebContent"],
    iri["schema:offers"]: ACTIONS["DemandOrOffer"],
    iri["schema:positiveNotes"]: ACTIONS["ItemListOrListItemOrWebContent"],
    iri["schema:size"]: ACTIONS["DefinedTermOrQuantitativeValueOrSizeSpecification"],
    iri["schema:weight"]: ACTIONS["MassOrQuantitativeValue"],
    iri["schema:width"]: ACTIONS["DistanceOrQuantitativeValue"]
}

CODEMETA_STRATEGY[iri["schema:ProductGroup"]] = {**CODEMETA_STRATEGY[iri["schema:Product"]]}
CODEMETA_STRATEGY[iri["schema:ProductModel"]] = {
    **CODEMETA_STRATEGY[iri["schema:Product"]],
    iri["schema:isVariantOf"]: ACTIONS["ProductGroupOrProductModel"]
}


CODEMETA_STRATEGY[iri["schema:Taxon"]] = {**CODEMETA_STRATEGY[iri["schema:Thing"]]}


CODEMETA_STRATEGY[iri["schema:CreativeWorkSeries"]] = {
    **CODEMETA_STRATEGY[iri["schema:CreativeWork"]],
    **CODEMETA_STRATEGY[iri["schema:Series"]]
}

CODEMETA_STRATEGY[iri["schema:DefinedRegion"]] = {
    **CODEMETA_STRATEGY[iri["schema:Place"]],
    **CODEMETA_STRATEGY[iri["schema:StructuredValue"]]
}

CODEMETA_STRATEGY[iri["schema:Drug"]] = {
    **CODEMETA_STRATEGY[iri["schema:Product"]],
    **CODEMETA_STRATEGY[iri["schema:MedicalEntity"]]
}

CODEMETA_STRATEGY[iri["schema:EducationalOrganization"]] = {
    **CODEMETA_STRATEGY[iri["schema:Organization"]],
    **CODEMETA_STRATEGY[iri["schema:CivicStructure"]]
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

CODEMETA_STRATEGY[iri["schema:MedicalCode"]] = {
    **CODEMETA_STRATEGY[iri["schema:CategoryCode"]],
    **CODEMETA_STRATEGY[iri["schema:MedicalIntangible"]]
}

CODEMETA_STRATEGY[iri["schema:PaymentCard"]] = {
    **CODEMETA_STRATEGY[iri["schema:FinancialProduct"]],
    **CODEMETA_STRATEGY[iri["schema:PaymentMethod"]]
}
CODEMETA_STRATEGY[iri["schema:CreditCard"]] = {
    **CODEMETA_STRATEGY[iri["schema:LoanOrCredit"]],
    **CODEMETA_STRATEGY[iri["schema:PaymentCard"]]
}
