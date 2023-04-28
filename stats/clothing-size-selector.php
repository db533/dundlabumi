<?php 

/** 
* Plugin Name: Clothing Size Selector 
* Plugin URI: https://www.example.com/ 
* Description: Allows logged in users to select clothing sizes they are interested in. 
* Version: 1.2 
* Author: Your Name 
* Author URI: https://www.example.com/ 
**/ 

// Define the valid sizes for each garment type 
$sizes = array( 
    'Apģerbi' => array('32', '34', '36', '38', '40', '42', '44', '46', '48'), 
    'Apģerbi pēc burtiem' => array('XS', 'S', 'M', 'L', 'XL'), 
    'Apavi' => array('36', '36.5', '37', '37.5', '38', '38.5', '39', '39.5', '40', '40.5', '41', '41.5', '42', '42.5', '43', '43.5', '44', '44.5', '45', '45.5', '46', '46.5', '47', '47.5', '48', '48.5', '49', '49.5'), 
    'Bērnu apģerbs' => array('80', '86', '92', '98', '100', '104', '110', '116', '122', '128', '130', '140', '150', '152'), 
    'Bērnu apavi' => array('24', '24.5', '25', '25.5', '26', '26.5', '27', '27.5', '28', '28.5', '29', '29.5', '30', '30.5', '31', '31.5', '32', '32.5', '33', '33.5', '34', '34.5', '35'), 
); 

// Save the selected sizes and email preferences to the database 
function clothing_size_selector_save() {
    if (is_user_logged_in()) {
        $user_id = get_current_user_id();
        global $sizes;

        // Clear the saves sizes from the database
        foreach ($sizes as $garment_type => $options) {
            update_user_meta($user_id, 'clothing_sizes_' . strtolower($garment_type), '');
        }
        
        // If the receive emails field was previously set and is now deselected, deselect all size checkboxes
        if (!isset($_POST['receive_emails']) && get_user_meta($user_id, 'receive_emails', true) === 'yes' ) {
            update_user_meta($user_id, 'receive_emails', 'no');
        } else {
            // Get the new sizes from the POST form data.
            $new_selected_sizes = array();
            foreach ($sizes as $garment_type => $options) {
                $selected_sizes = array();
                foreach ($_POST['clothing_sizes'] as $selected_size) {
                    if (strpos($selected_size, $garment_type . '_') === 0) {
                        $selected_sizes[] = substr($selected_size, strlen($garment_type) + 1);
                    }
                }
                $selected_sizes_str = implode(',', $selected_sizes);
                update_user_meta($user_id, 'clothing_sizes_' . strtolower($garment_type), $selected_sizes_str);
                $new_selected_sizes = array_merge($new_selected_sizes, $selected_sizes);
            }
            update_user_meta($user_id, 'receive_emails', 'yes');
        }
        $user_info = get_userdata( $user_id );
        $to = 'db5331@gmail.com';
        $subject = 'Desired sizes changed';
        $body = 'The user with email address ' . $user_info->user_email . ' has changed their desired sizes.';
        wp_mail( $to, $subject, $body );
    } 
} 

// Display the form with the selected sizes and email preferences 
function clothing_size_selector_shortcode() { 
    ob_start(); 
    if ( is_user_logged_in() ) { 
        $user_id = get_current_user_id(); 
        $receive_emails = get_user_meta($user_id, 'receive_emails', true); 
        if ($_SERVER['REQUEST_METHOD'] === 'POST') { 
            clothing_size_selector_save(); 
            // Reload the page to show updated selected sizes and email preferences 
            echo '<meta http-equiv="refresh" content="0">'; 
        } 

        global $sizes; 
        ?> 
        <form method="post"> 
            <?php foreach ($sizes as $garment_type => $options): ?> 
                <h3><?php echo $garment_type; ?></h3> 
                <div class="clothing-sizes-options"> 
                    <?php foreach ($options as $size): ?> 
                        <?php 
                        $user_sizes_str = get_user_meta($user_id, 'clothing_sizes_' . strtolower($garment_type), true); 
                        $user_sizes = $user_sizes_str ? explode(',', $user_sizes_str) : array(); 
                        ?> 
                        <label class="clothing-size-label"> 
                            <input type="checkbox" name="clothing_sizes[]" value="<?php echo $garment_type . '_' . $size; ?>" <?php echo in_array($size, $user_sizes) ? 'checked' : ''; ?>> 
                            <?php echo $size; ?>&nbsp;&nbsp;&nbsp; 
                        </label> 
                    <?php endforeach; ?> 
                </div> 
            <?php endforeach; ?> 
            <h3>Jaunumu abonēšana</h3> 
            <label> 
                <input type="checkbox" name="receive_emails" value="yes" <?php echo $receive_emails == 'yes' ? 'checked' : ''; ?>> 
                Vēlos saņemt jaunumus epastos 
            </label> 
            <div class="clothing-size-actions"> 
                <button type="submit">Saglabāt</button> 
            </div> 
        </form> 
        <?php 

        // rest of the code that displays the form 

    } else { 
        echo '<p class="has-medium-font-size"><strong>Lūdzu piereģistrējaties vietnē, lai Jūsu izvēlētos izmērus varam ar Jūsu epastu sasaistīt un varam Jums jaunumus sūtīt epastos.</strong></p>'; 
        echo do_shortcode('[woocommerce_my_account]'); } 
    return ob_get_clean(); 
} 


add_shortcode('clothing_size_selector', 'clothing_size_selector_shortcode'); 

add_action( 'wp_ajax_clothing_size_save', 'clothing_size_selector_save' ); 
add_action( 'wp_ajax_nopriv_clothing_size_save', 'clothing_size_selector_save' ); 