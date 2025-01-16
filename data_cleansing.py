""" Class for the cleansing of the Real Estate data provided. """

# Importing required libraries
import folium
import pandas as pd
import numpy as np
import re


class DataCleansing:
  
    def __init__(self, data: pd.DataFrame = pd.DataFrame(),
                 mapping_data: pd.DataFrame = pd.DataFrame()):
        
        self.data = data
        self.mapping_data = mapping_data
    
    def commaReplace(self, column):
        '''
        Parameters
        column: represents the column which is eligible for cleansing.

        Returns
        The initial dataframe after replacing the comma character with a dot
        in order for the values of the column to be considered float numbers.
        '''
        self.data[column] = self.data[column].str.replace(',', '.')
        self.data[column] = self.data[column].astype(float)
        
        return self.data[column]
    
    def priceColumn(self, price, price_m2, area):
        '''
        Parameters
        price: represents the column containing the price of the property.
        price_m2: represents the column containing the price per square meter.
        area: represents the column containing the square meters of the
              property of interest.

        Returns
        The initial dataframe after creating an additional column
        (price_verif) for verification of the price column and replacing the
        problematic values of the price column.
        '''
        self.data['price_verif'] = (self.data[price_m2]*self.data[area])/1000
        self.data['price_verif'] = (self.data['price_verif'].round() *
                                    1000).astype(int)
        
        # Finding the records that correspond to these problematic values
        indices_list = self.data[price][~pd.to_numeric(
            self.data[price], errors='coerce').notna()].index
        
        # Replacing the price with the corresponding values from price_verif
        self.data.loc[indices_list, price] = self.data.loc[
            indices_list, 'price_verif'].copy()
        
        # Removing the price_verif column that we created
        self.data.drop('price_verif', axis=1, inplace=True)
        
        # Verifying that both price and price_m2 columns are of float type
        self.data[price] = self.data[price].astype(float)
        self.data[price_m2] = self.data[price_m2].astype(float)
        
        return self.data[price]
    
    def propertyTypeMapping(self, property_type):
        '''
        Parameters
        property_type: represents the property type column which is eligible
                       for cleansing.

        Returns
        The initial dataframe after mapping the different values that the
        property type column can take to specific types of property.
        '''
        # Converting to lowercase for case-insensitive matching
        self.data[property_type] = self.data[property_type].str.lower()
        
        # Mapping the values that finds to contain a certain string to a
        # corresponding property type
        self.data.loc[self.data[property_type].str.contains('ll|villa'),
                      property_type] = 'Villa'
        self.data.loc[self.data[property_type].str.contains('apa|rt|apart'),
                      property_type] = 'Apartment'
        self.data.loc[self.data[property_type].str.contains('st|stud'),
                      property_type] = 'Studio Flat'
        
        return self.data[property_type]
    
    def parkingMapping(self, has_parking):
        '''
        Parameters
        has_parking: represents the has_parking column which is eligible
                     for cleansing.

        Returns
        The initial dataframe after mapping the different values that the
        has_parking column can take for each property.
        '''
        # Converting to lowercase for case-insensitive matching
        self.data[has_parking] = self.data[has_parking].str.lower()
        
        # Mapping the values that finds to contain a certain string to a
        # corresponding value (1 if the property has parking, 0 otherwise)
        self.data.loc[self.data[has_parking].str.contains('y|yes|true|tr'),
                      has_parking] = 'Yes'
        self.data.loc[self.data[has_parking].str.contains('n|no|false|f'),
                      has_parking] = 'No'
        
        return self.data[has_parking]
    
    def bedroomsMapping(self, bedrooms):
        '''
        Parameters
        bedrooms: represents the number of bedrooms column of each property
                  which is eligible for cleansing.

        Returns
        The initial dataframe after mapping the different values that the
        bedrooms column can take for each property.
        '''
        # Keeping only the numeric values from the strings that contain both
        # the number of bedrooms and additional text
        self.data[bedrooms] = self.data[bedrooms].apply(
            lambda x: int(x.split(',')[0].strip()) if ',' in x else int(
                re.findall(r'\d+', x)[0]))
        # this regex keeps only the integer value that it finds first before a
        # comma and it also extracts the number from a string and not the text
        
        return self.data[bedrooms]
    
    def fix_coordinate(self, value):
        '''
        Parameters
        value: represents the large value included in the latitude or
               longitude column which is eligible for cleansing.

        Returns
        The value after being converted to the appropriate format to be
        considered as coordinate.
        '''
        # If the value is a float or integer and has more than 8 digits, adjust
        if isinstance(value, (int, float)):
            # Convert the number to a string to easily check its length
            value_str = str(value)
            
            # Check if it's a large number (more than 8 digits)
            if len(value_str.replace('.', '').lstrip('0')) > 8:
                # Find the number of digits (excluding leading zeros)
                num_digits = len(value_str.replace('.', '').lstrip('0'))
                
                # Place the decimal after the first two digits, after
                # making sure that there are no dots from int-float numbers
                if num_digits > 2:
                    value_str = value_str.replace('.', '')
                    value_str = value_str[:2] + '.' + value_str[2:]
                value = float(value_str)  # Convert back to float
                
        return value
    
    def coordinatesColumns(self, coordinate):
        '''
        Parameters
        coordinate: represents either the latitude or the longitude column
                    which is eligible for cleansing.

        Returns
        The initial dataframe after correcting the different problematic
        values that the latitude/longitude columns take for each property.
        '''
        self.data[coordinate] = self.data[coordinate].str.replace('-', '')
        self.data[coordinate] = self.data[coordinate].str.replace(',', '.')
        # Replacing all missing values with 0
        self.data[coordinate].fillna(0, inplace=True)
        self.data[coordinate].replace("", 0, inplace=True)
        self.data[coordinate] = self.data[coordinate].astype(float)
        
        indices_list = self.data.loc[self.data[coordinate] > 100].index
        
        self.data.loc[indices_list, coordinate] = self.data.loc[
            indices_list, coordinate].apply(self.fix_coordinate)
        
        return self.data[coordinate]
    
    def mapPlotting(self, lat, lng, locality):
        '''
        Parameters
        lat: represents the latitude of a location on the map.
        lng: represents the longitude of a location on the map.
        locality: represents a location on the map.

        Returns
        A map with the different locations on it circled with red color and
        blue dots.
        '''
        # Instantiating a feature group
        greece_reg = folium.map.FeatureGroup()
        
        # Creating a Folium map centered on Greece
        greece_map = folium.Map(location=[self.mapping_data[lat].iloc[0],
                                          self.mapping_data[lng].iloc[0]],
                                zoom_start=4)
        
        # Looping through the region and adding to feature group
        for lat, lng, loc in zip(self.mapping_data[lat],
                                 self.mapping_data[lng],
                                 self.mapping_data[locality]):
            greece_reg.add_child(
                folium.features.CircleMarker(
                    [lat, lng],
                    popup=loc,
                    radius=4,  # defining how big the circle markers will be
                    color='red',
                    fill=True,
                    fill_color='blue',
                    fill_opacity=0.6
                )
            )
        
        # Adding incidents to map
        return greece_map.add_child(greece_reg)
    
    def missingLocationMapping(self, lat, lng, location):
        '''
        Parameters
        lat: represents the latitude of a location on the map.
        lng: represents the longitude of a location on the map.
        location: represents a location on the map.

        Returns
        A new dataframe of the dataset with the records, for which there is no
        location available, mapped through the mapping file
        (based on coordinates).
        '''
        # Finding the values for which neither location nor coordinates are
        # provided in the datatape
        self.data[location].fillna('-', inplace=True)
        
        # For these cases, the description "No location" is appointed,
        # instead of disregarding-removing entirely the observations
        self.data.loc[((self.data[location] == '-') &
                       (self.data[lat] == 0) &
                       (self.data[lng] == 0)), location] = 'No location'
        
        # Rounding the columns with coordinates at the mapping dataset
        self.mapping_data[lat] = self.mapping_data[lat].round(5)
        self.mapping_data[lng] = self.mapping_data[lng].round(5)
        
        # Merging the 2 dataframes based on the coordinates
        df_first_mapping = self.data.merge(self.mapping_data, how='left',
                                           on=[lat, lng])
        
        # Replacing the location for the cases where this location='-'
        # with the value from the mapping file for this location
        df_first_mapping[location] = np.where(
            df_first_mapping[location].str.contains('-'),
            df_first_mapping['Locality'], df_first_mapping[location])
        
        return df_first_mapping
    
    def missingCoordinatesMapping(self, lat, lng, location, df_first_mapping):
        '''
        Parameters
        lat: represents the latitude of a location on the map.
        lng: represents the longitude of a location on the map.
        location: represents a location on the map.
        df_first_mapping: represents the dataframe from the first mapping
                          (based on coordinates from the mapping file) for the
                          cases of missing location.

        Returns
        A new dataframe of the dataset with the records, for which there is
        no location, mapped through the mapping file (based on coordinates).
        '''
        # Renaming the Locality column of the mapping file to location
        self.mapping_data = self.mapping_data.rename(
            columns={'Locality': 'location',
                     lat: 'lat_mapping',
                     lng: 'lng_mapping'})
        
        # Merging the 2 dataframes (df_first_mapping, mapping_data)
        # based on the location
        df_second_mapping = df_first_mapping.merge(
            self.mapping_data, how='left', on=['location'])
        
        # Replacing the latitude for the cases where this coordinate=0
        # with the value from the mapping file for this location
        df_second_mapping[lat] = np.where(df_second_mapping[lat] == 0,
                                          df_second_mapping['lat_mapping'],
                                          df_second_mapping[lat])
        
        # Replacing the longitude for the cases where this coordinate=0
        # with the value from the mapping file for this location
        df_second_mapping[lng] = np.where(df_second_mapping[lng] == 0,
                                          df_second_mapping['lng_mapping'],
                                          df_second_mapping[lng])
        
        # Removing the unnecessary columns which have been merged
        df_second_mapping.drop(['lat_mapping', 'lng_mapping'],
                               axis=1, inplace=True)

        return df_second_mapping


  